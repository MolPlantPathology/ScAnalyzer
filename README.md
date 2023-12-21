# ScAnalyzer
ScAnalyzer is an image processing tool developped in the Molecular Plant Pathology lab of the University of Amsterdan, the Netherlands. The purpose of the tool is to monitor disease symptoms and bacterial spread in *Arabidopsis thaliana* leaves.

## Installation and dependencies
To install ScAnalyzer, first download the GitHub repo, either by cloning the repository of by simply downloading the .zip file from GitHub. Because ScAnalyzer relies on several dependencies (most importantly, the python library openCV, and specific versions of R packages for the autoplot function), it is recommended to use an environment manager such as [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html). Use the `scanalyzer.yaml` file to create a new conda environment with all dependencies preinstalled.
```
conda env create -f scanalyzer.yml
```
Then activate the environment
```
conda activate scanalyzer
```
If you do not want to use conda, just clone the GitHub repo, and make sure that the most important dependencies are installed: `Python version 3.11.0`, `cv2 version 4.7.0`, `R version 4.2.0`, with the following packages loaded `readr_2.1.4 dplyr_1.1.3 ggpubr_0.4.0 patchwork_1.1.1 ggplot2_3.4.4`.

## Compatibility
ScAnalyzer was developped and extensively tested in macOS Mojave. Other operating systems were not tested.

## Before running ScAnalyzer
ScAnalyzer is optimized to study leaves of four to six week old *Arabidopsis thaliana* plants. Perform a disease assay with bacterial pathogens tagged with a bioluminescence operon. Then, sample your infected leaves and glue them onto a sheet of paper on which the supplied `grid.pdf` is printed. Detect the bacterial bioluminescence using light-sensitive films (see [van Hulten *et al*., (2019)](https://link.springer.com/protocol/10.1007/978-1-4939-9458-8_16) and [Paauw *et al*., (2023)](https://pubmed.ncbi.nlm.nih.gov/36731466/)). Then, scan both the leaf samples and the light-senstive film in a A3 flatbed scanner. *Note*: in order to automatically overlay the leaf samples with the film samples, the leaf scan and the film scan should be perfectly aligned. If they are not, ScAnalyzer *will not* fix this for you, and the numerical data output may not make sense. If in doubt, overlay your leaf scan with your film scan in e.g. Adobe Photoshop, and manually adjust the alignment if required. Make a samplelist `.csv` file to connect experimental variables to each individual sample (e.g. plant genotype, days post inoculation, ...).

## Running ScAnalyzer
To run ScAnalyzer you need to specify several arguments. They are described below. This help message can also be printed to your local console by running `python3 scanalyzer.py -h`.
```
usage: scanalyzer.py [-h] -leaves LEAVES -film FILM -samples SAMPLES -prefix PREFIX [--autoplot]

ScAnalyzer v0.1

options:
  -h, --help        show this help message and exit
  -leaves LEAVES    The scan of the leaves (.jpg)
  -film FILM        The scan of the film displaying bacterial presence (.jpg)
  -samples SAMPLES  The samplelist (.csv)
  -prefix PREFIX    Prefix for the output files
  --autoplot        Activate autoplot function
````
## Example: Running ScAnalyzer
To run ScAnalyer on the provided samples, run the following command:
```bash
python3 scanalyzer.py -leaves M65M66_14dpi_l.jpg -film M65M66_14dpi_s.jpg -samples M65M66_14dpi.csv -prefix M65M66_14dpi --autoplot
```
This gives you two new `.jpg` files with the leafs and the bacterial bioluminescence data, annotated with the area that has been detected by ScAnalyzer. In addition, you should get the output datatable, and an automatically generated plot for quick insights in your data. If you don't want the autoplot, simply omit the `--autoplot` flag.

## Example: Combining multiple experiments
Often, experiments can contain more samples than the 126 that fit on one sampling sheet. In that case, process different sample sheets indepedently. Then combine the output files either manually (in e.g. Excel) or on the command line:
```bash
cat M65M66_10dpi_data.csv > M65M66_total_data.csv

# use tail -n +2 to avoid duplicating the header the the final datafile.
tail -n +2 M65M66_14dpi_data.csv >> M65M66_total_data.csv   
```
Then, you can run the autoplotter (without running ScAnalyzer) to make a quick plot for your full experiment:
````
Rscript autoplotter.R M65M66_total_data.csv
````
Alternatively, you can explore the data yourself.

## Adapting ScAnalyzer to your lab
You may need to adapt ScAnalyzer in your lab. For example, your image conditions may be different. In that case, you could try to adapt the thresholds to detect the leaf itself (line xx ), to seperate chlorotic from healthy tissue (line xx), or to select the bacteria colonized area (line xx). Be sure to record this carefully and report the thresholds used in your analysis.

## Citation
If ScAnalyzer was useful for your work, please cite:
```
Paauw, M., Hardeman, G., Pfeilmeier, S., van den Burg, H.A., ScAnalyzer: an image processing tool to monitor disease symptoms and bacterial spread in Arabidopsis thaliana leaves. *Journal title* (2024).
```
