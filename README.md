# PacificStormwater
Estimate urban stormwater contaminant load to the Pacific Ocean from the West Coast of the United States.

Workflow: CollateLU.py ->  RoadLU.py

In short:
- Collate all available land use data for California
- Rasterize California zoning/land use, keeping the most recent dataset for each pixel (see data sources for details on what datasets were used) - 30 m
- Rasterize statewide zoning/land use datasets for Oregon and Washington - 30 m
- Mosaic raster of all three states
- Reclassify NLCD using mosaicked raster:
  - Developed, Open Space  (NLCD 21) -> Not reclassified (stays 21), because close inspection showed that it almost only includes city parks and golf courses
  - Developed, Low and Medium Intensity (NLCD 22, 23) -> Residential (97)
  - Developed High Intensity (24) & (commercial zoning or any other zoning) -> Commercial (98)
  - Developed High Intensity (24) & (industrial zoning)  -> Industrial (99)
- Merge Open Street Map roads for all three states
- Subset roads to exclude pedestrian streets, tracks, bus_guideway, and escape
- Buffer road vector with the following rules:
  - Assume lanes of 12ft, the most common width standard  (https://safety.fhwa.dot.gov/geometric/pubs/mitigationstrategies/chapter3/3_lanewidth.cfm)
  - For all roads but motorways and trunks, assume two 12-ft lanes (to account for two ways) and no shoulder adding to lane width
  - For motorway (e.g. interstate), assume three lanes each way + 1-sided 10 ft outside shoulder and inside 4ft shoulder
  - For trunk, assume same thing as motorway but two lanes each way
- Rasterize road buffers to 6 m resolution snapped to NLCD_reclass
- Aggregate road raster to 30 m, computing the number of subpixels (out of 25) in each 30 m cell that is considered a road
- Further reclassify NLCD using road raster and NLCD impervious surface dataset (% imperviousness in each cell):
For any developed pixel (21, 97, 98, 99), if road covers more than 50% of the impervious area in the developed pixel (100*road_raster/(25*imperviousness) > 0.50) ->  road (96) 
