# Power BI reference assets

This folder contains a DAX measures reference and a JSON theme proposal. The
existing `Ecommerce_Business_Analytics.pbix` is a 1.7 KB package stub with no
semantic model, loaded data, relationships, or usable visuals. It is excluded
from Git and must not be presented as an interactive report.

The repository's runnable dashboard is a separate local web prototype in
[`../dashboard/`](../dashboard/). It queries `data/ecommerce_analytics.db` and
supports page navigation plus Year, Region, Category, Sales Channel, and
Customer Segment filters. The six PNGs in `screenshots/` are regenerated
captures of that prototype; they are not Power BI screenshots.

The DAX file is a reference only. Its measures have not been validated in a
Power BI model, and measures requiring relationships or time-intelligence
configuration are not guaranteed to work without model authoring and testing.

## Creating a real Power BI report

Open Power BI Desktop, import the cleaned CSV tables or the SQLite warehouse
through an appropriate connector, define and verify the model relationships,
add the measures from `dax_measures_reference.dax`, then build and test the
report pages and slicers. Save the authored report as a PBIX only after these
steps; no PBIX generation is claimed by this repository.
