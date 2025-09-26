# Useful References

## Alaska Satellite Facility (ASF)

### Product Guide

- [Types of SAR Products](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/types-sar-products)
- [Sentinel-1 RTC Product Guide](https://hyp3-docs.asf.alaska.edu/guides/rtc_product_guide/)
- [Sentinel-1 InSAR Product Guide](https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/)
- [**Exploring Sentinel-1 InSAR**](https://storymaps.arcgis.com/stories/8be186e4125741518118d0102e6835e5) : step by step explanation of the InSAR outputs

> One of the most common hurdles when working with Sentinel-1 data is the process of transforming available Level 1 data (SLC or GRD) to an analysis-ready format. Because of the side-looking geometry of the image acquisition, there are distortions inherent to SAR datasets that need to be corrected before they can be used in GIS applications.  [**Radiometric Terrain Correction (RTC)**](https://hyp3-docs.asf.alaska.edu/guides/rtc_product_guide/)  uses a  [Digital Elevation Model (DEM)](https://hyp3-docs.asf.alaska.edu/guides/rtc_product_guide/#digital-elevation-models)  to adjust for these distortions, generating a product that is ready for GIS analysis.

### Background Knowledge

#### Santinel-1

Sentinel-1 offers global coverage with **C-Band SAR**. Sentinel-1A was launched in 2014, and Sentinel-1B was launched in 2016. Each satellite has a **12 day repeat cycle**, and **some areas have coverage every 6 days**. New acquisition data is available to download within 3 days, though it is most often available within 24 hours. The data is free and easy to download in several formats.

#### GRD

Ground Range Detected (GRD) products are best for amplitude applications, such as generating RTC images. These are Level 1 products. These products are georeferenced, and multi-looked into a single image. Only amplitude information is included in the GRD.

- No effort required to view data in a GIS software
- Easy to project to desired coordinate system
- Pixels are in ground-detected geometry
- One consolidated image for each polarization
- Square pixels
- Smaller file size

#### SLC

Single Look Complex (SLC) products are necessary for interferometry. These are Level 1 products. These products are comprised of 3 GeoTIFFs, one for each of the sub-swaths, and each radar burst is included in the data. The SLC includes phase data.

- Remains in slant-range geometry
- Phase data is retained
    - Suitable for detecting changes in surface elevation
    - Required for generating interferograms
- Several images for each SLC
- Retains each subswath (including overlap) and series of bursts, with a black line grid

#### DEM

- [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

A Digital Elevation Model (DEM) is required for radiometric terrain correction. The [GLO-30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM "Copernicus DEM") is used to process all RTC On Demand products.

#### Wrapped

The wrapped interferogram displays the phase differences between two SAR acquisitions. These phase differences are constrained to a 2π scale, equivalent to one-half of the wavelength of the SAR sensor.

[Sentinel-1](https://sentiwiki.copernicus.eu/web/s1-mission)  has a C-band SAR sensor, with a wavelength of about 5.6 cm, so a 2π difference would be equivalent to about 2.8 cm.

The wrapped interferogram is often most useful as a visualization with a cyclic color ramp applied. Each pass through the color cycle - often called a "fringe" - is equivalent to a displacement of 2.8 cm in the line of sight of the sensor.

#### Unwrapped

To automate the conversion of fringes to line-of-sight displacement, phase unwrapping algorithms have been developed. The approach used for these InSAR products is  [Minimum Cost Flow (MCF)](https://www.gamma-rs.ch/uploads/media/2002-5_TR_Phase_Unwrapping.pdf) .

This automated approach essentially does the counting for you, assigning multiples of consecutive integers to the fringes starting from a reference point. Measurements are converted from the constraints of a 2π cycle to a continuous range of consecutive multiples of 2π.

## Usecases

### SAR for Detecting and Monitoring Floods, Sea Ice, and Subsidence from Groundwater Extraction

- [SAR for Detecting and Monitoring Floods, Sea Ice, and Subsidence from Groundwater Extraction](https://www.earthdata.nasa.gov/learn/trainings/sar-detecting-monitoring-floods-sea-ice-subsidence-from-groundwater-extraction)

**Sessions:**

- Detecting and Monitoring Floods with SAR
- Detecting and Monitoring Sea Ice with SAR
- Measuring Surface Subsidence from Groundwater Extraction with InSAR

### Secrets Beneath the Sand

- [Secrets Beneath the Sand](https://earthobservatory.nasa.gov/images/90847/secrets-beneath-the-sand)