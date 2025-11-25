## Dataset and Analysis Assumptions

This project revolves around one CSV dataset and a small set of rules for how I interpret each row. This section is meant to read like design notes you might find in a real codebase: what data I used, how I clean it, and what exactly goes into each analysis view.

---

### Dataset in Use

* **Name:** Online Retail II
* **Source:** UCI Machine Learning Repository
* **File used in this project:** `data/online_retail.csv` (CSV export of the original Excel workbook)
* **Scope:** Transaction‑level event log from a UK‑based online retailer, roughly 2009–2011, in GBP.

The analysis code relies on these columns:

| Column        | Meaning                                                                |
| ------------- | ---------------------------------------------------------------------- |
| `InvoiceNo`   | Invoice identifier; values starting with `C` are cancellations/credits |
| `StockCode`   | Product code                                                           |
| `Description` | Product name (may be missing)                                          |
| `Quantity`    | Units in this line (negative values represent returns)                 |
| `InvoiceDate` | Date/time of the invoice                                               |
| `UnitPrice`   | Price per unit in GBP                                                  |
| `CustomerID`  | Numeric customer ID                                                    |
| `Country`     | Customer country                                                       |

Each row is a **single line item**, not a pre‑aggregated fact. That makes it a good fit for streaming, filtering, and group‑by style operations.

---

### Why This Dataset Works for the Assignment

The assignment asks for stream‑style CSV processing with functional patterns and aggregations. This dataset fits that brief nicely:

* It is **large enough** that using generators and one‑pass aggregations actually matters.
* It is **low‑level** (per line item) so grouping by country, month, customer, or product is natural.
* It has **real‑world quirks**: missing IDs, cancellations, odd or messy rows. That lets me make explicit assumptions instead of pretending the data is perfect.

In short, it behaves like production data: useful, but a little messy, and that is exactly what I wanted to demonstrate.

---

### Loading and Cleaning Rules

All ingestion logic lives in `src/io_utils.py` and `src/models.py`. The goal is to keep the rules simple, predictable, and easy to change later.

#### 1. Header normalization

A small map (`HEADER_MAP`) converts common header variants into a canonical schema used in the code. For example:

* `Invoice` → `InvoiceNo`
* `Price` → `UnitPrice`
* `Customer ID` → `CustomerID`

This lets the loader accept slightly different header spellings without changing the analysis code.

#### 2. Type parsing

* `Quantity` is parsed as `int`.
* `UnitPrice` is parsed as `float`.
* `InvoiceDate` is parsed into a `datetime` using several allowed formats.

If any of these fail, the row is **skipped**. For this assignment, I prefer "skip clearly broken rows" over "try to guess and maybe corrupt the metrics".

#### 3. Required fields

Rows missing any of these are also dropped:

* `InvoiceNo`
* `StockCode`
* `Country`
* A valid `InvoiceDate`

This keeps downstream aggregations simple and avoids having to special‑case half‑missing records later.

#### 4. Transaction model

Every accepted row becomes a `Transaction` dataclass instance. Two properties are used throughout the analysis:

* `line_total = quantity * unit_price`
* `is_cancellation = invoice_no.upper().startswith("C")`

These properties keep the rest of the code readable: functions can talk in terms of "line total" and "cancellation" instead of re‑implementing those checks.

---

### Sales View vs Returns View

Conceptually, the analysis splits the stream into two views:

#### Sales view (`valid_transactions`)

This is the basis for the headline KPIs:

* Total revenue
* Revenue by country
* Monthly revenue
* Top products
* Top customers
* Average order value
* Units sold per product
* Sales by weekday

A row is treated as a **valid sale** if all of the following hold:

* It is **not** a cancellation (`not t.is_cancellation`)
* `Quantity > 0`
* `UnitPrice > 0.0`

In code, this is the `valid_transactions(records)` generator. Everything that does not meet these criteria is excluded from the "sales view".

#### Returns / cancellations view (`returns_view`)

Returns and cancellations are still important, they just live in their own view. A row belongs here if:

* `t.is_cancellation` is `True`, **or**
* `t.quantity <= 0`

The `returns_view(records)` generator yields exactly those records. This makes it easy to build cancellation/returns metrics without mixing them into normal sales.

---

### Cancellations and Cancellation Rate

Cancellations are summarised in two ways, using the full raw stream.

#### 1. Invoice‑level summary (`cancellation_summary`)

This function:

* Tracks all distinct invoice IDs.
* Marks invoices that contain cancellations or non‑positive quantities.
* Computes:

  * `TotalCancellations` – how many invoices were affected.
  * `CancellationRate` – percentage of all invoices that had cancellations.
  * `CancelledNetAmount` – signed sum of line totals for cancelled/negative rows.
  * `CancelledAbsAmount` – absolute amount, i.e. magnitude of cancelled volume.

This answers questions like "how common are cancellations" and "what is the net financial impact".

#### 2. Volume share of cancellations (`cancellation_rate`)

Here the question is: *what fraction of our monetary volume gets cancelled?*

* `gross` = sum of absolute line totals for **all** rows.
* `cancelled` = sum of absolute line totals where `is_cancellation` or `quantity <= 0`.
* Return value = `(cancelled / gross) * 100.0` (or `0.0` if `gross` is zero).

Together, these two functions give both an invoice‑level rate and a revenue‑level rate for cancellations.

---

### Handling Missing Descriptions and Customer IDs

The Online Retail II data occasionally drops some fields. Two common cases are missing descriptions and missing customer IDs.

#### Product naming

For any metric keyed by product, the code:

* Uses `Description.strip()` when it is present and non‑empty.
* Falls back to `StockCode` when the description is missing.

This behaviour is implemented in a helper (`_product_key`) and reused by:

* `top_n_products_by_revenue`
* `units_sold_per_product`

That way, I keep as much useful data as possible without creating mysterious "Unnamed" buckets.

#### Customer attribution

* For **global** metrics (total revenue, revenue by country/month, product metrics), rows with missing `CustomerID` are **included**. They still represent real sales.
* For **customer‑level** metrics (`top_n_customers_by_revenue`), rows with missing `CustomerID` are **ignored**, because there is no reliable way to assign that revenue to a specific customer.

This strikes a balance between not wasting sales data and keeping customer rankings logically correct.

---

### What These Choices Give Us

These rules are all implemented as small, composable functions, which keeps the analysis close to a functional and streaming style:

* `load_transactions` yields one `Transaction` at a time from the CSV.
* `valid_transactions` and `returns_view` are pure filters over that stream.
* Aggregations like `total_revenue`, `revenue_by_country`, `monthly_revenue`, and the various "top N" helpers are dictionary folds with lambda‑based sorting.

For a reviewer, the important part is that none of the behaviour is "magic": every assumption about what counts as a sale, how cancellations are treated, or how missing data is handled is both documented here and backed by a clear function in the code.
