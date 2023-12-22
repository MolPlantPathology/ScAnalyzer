#!/usr/bin/Rscript
suppressPackageStartupMessages({
  library(readr)
  library(ggplot2)
  library(dplyr)
  library(patchwork)
})

# Get the filename from the command line argument, generate outfile names based on infile name
args = commandArgs(trailingOnly=TRUE) # enable command line argument 
infile <- args[1]
prefix <- sub(".csv", "", infile)
outfile_png <- paste(prefix,"_autoplot.png", sep="")
outfile_pdf <- paste(prefix,"_autoplot.pdf", sep="")


# setwd("/Users/misha/surfdrive/12_Automatic Film Analysis/2023_development")

# some layout settings
theme_mp <- theme_bw() +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank()) +
  theme(strip.text = element_text(size = 8,  margin = margin(t = 3, b = 3))) +
  theme(strip.background = element_rect(fill = "grey90")) +
  theme(axis.text=element_text(colour="black")) +
  theme(legend.key.size = unit(0.6, "cm")) +
  theme(legend.position = "right") +
  theme(text = element_text(size = 8, family="sans", colour = "black")) +
  theme(axis.text = element_text(size = 8, family="sans", colour = "black")) +
  theme(axis.title = element_text(size = 8, family="sans", colour = "black"))

dataf <- read_csv(infile, show_col_types = FALSE)

# turning some variables into factors q
df <- dataf %>% mutate_at(c("bioassay", "genotype", "treatment", "dpi", "pathogen"), as.factor) %>% na.omit()

### TODO: calculate bacteria area (percentage) en chlorotic area (percentage)

# here we count the variables that have the highest number of levels (to organize which plots we will make)
counts <- df %>% sapply(nlevels) %>% sort(decreasing = TRUE)
x_var <- names(counts[1])
facet1 <- names(counts[2])
facet2 <- names(counts[3])
y_var <- "bacteria_area"

n_above1 <- sum(counts > 1)

# ggplot(data = df, aes_(y = value, x = as.name(x_var), color = as.name(group_var))) + geom_boxplot() + facet_grid(facet1~facet2) + theme_bw()

## TODO: should we print this information? 
## TODO: should i terminate the program if there are to many levels?
if(n_above1 == 1) {
  print("There's one variable with multiple levels, proceeding with a simple plot")
} else if(n_above1 == 2) {
  print("You have 2 variables with multiple levels, proceeding with a facetted plot")
} else if(n_above1 ==3) {
  print("You have 3 variables with multiple levels, proceeding with a double facetted plot")
} else {
  print("You have 4 variables with multiple levels, please plot this yourself")
}


       

#model <- kruskal.test(bacteria_area ~ genotype, data = df)
#post_hoc <- df %>% group_by(dpi, bioassay) %>% dunn_test(bacteria_area ~ genotype) # These are nice post hocs seperated by the facetting variables, but it's so far not possible to peel out the 'significance letters' (compact letter display)


## let's try ggpubr
library(ggpubr)
df2 <- df %>% dplyr::select(c(-1,-2))

####### Plot bacteria area
p <- ggplot(data = df, aes(y = .data[[y_var]], x = .data[[x_var]])) +
  geom_boxplot(aes(fill = .data[[x_var]]), outlier.shape = NA, alpha = 0.3) + geom_jitter(aes(color = .data[[x_var]]), width = 0.2, height = 0) + 
  facet_grid(as.formula(paste(facet2, " ~ ", facet1))) + 
  ylim(0, NA) +
  theme_mp

p1 <- p + stat_compare_means(label = "p.format", method = "kruskal.test", hide.ns = TRUE, tip.length = 1, size = 3, label.y = max(df$bacteria_area)/100*95)


y_var <- "chlorotic_area"

p <- ggplot(data = df, aes(y = .data[[y_var]], x = .data[[x_var]])) +
  geom_boxplot(aes(fill = .data[[x_var]]), outlier.shape = NA, alpha = 0.3) + geom_jitter(aes(color = .data[[x_var]]), width = 0.2, height = 0) + 
  facet_grid(as.formula(paste(facet2, " ~ ", facet1))) + 
  ylim(0, NA) +
  theme_mp

p2 <- p + stat_compare_means(label = "p.format", method = "kruskal.test", hide.ns = TRUE, tip.length = 1, size = 3, label.y = max(df$chlorotic_area)/100*95)


y_var <- "leaf_area"

p <- ggplot(data = df, aes(y = .data[[y_var]], x = .data[[x_var]])) +
  geom_boxplot(aes(fill = .data[[x_var]]), outlier.shape = NA, alpha = 0.3) + geom_jitter(aes(color = .data[[x_var]]), width = 0.2, height = 0) + 
  facet_grid(as.formula(paste(facet2, " ~ ", facet1))) + 
  ylim(0, NA) +
  theme_mp

p3 <- p + stat_compare_means(label = "p.format", method = "kruskal.test", hide.ns = TRUE, tip.length = 1, size = 3, label.y = max(df$leaf_area)/100*95)

# glue three plots together in one 'collage', using the patchwork package
collage <- (p1 / p2 / p3)


ggsave(outfile_png, collage, width = 16, height = 22, units = "cm", dpi = 300)
ggsave(outfile_pdf, collage, width = 16, height = 22, units = "cm", dpi = 300)








