## Set up script loading libraries and often-used packages

# Load libraries --------------------------------------------------------------------
setwd("~/Dropbox/Programmering/Python/masteroppgave")
library(tidyverse)
library(scales)
library(ggrepel)
library(ggridges)
library(patchwork)
library(janitor)
library(broom)
library(corrr)
# library(extrafont)

# Set theme --------------------------------------------------------------------
master_theme <- theme_minimal() +
	theme(
		text = element_text(family = 'Palatino', size = 24),
		plot.title = element_text(face = 'bold'),
		legend.position = 'bottom'
	)
theme_set(master_theme)

dpi <- 300
width <- 12
height <- 6.75
path <- 'results/plots/'

highlights <- c('Trondheim', 'Stjørdal', 'Namsos', 'Oppdal', 'Frøya', 'Røyrvik')
colors <- tibble(
	municipality = highlights,
	color = viridis::mako(length(municipality), begin = 0.3, end = 0.8)
)
default_color <- 'black'


# Load municipalities --------------------------------------------------------------------
municipalities <- read_csv('data/municipalities_data.csv', col_types = cols()) %>% 
	left_join(colors, by = 'municipality') %>% 
	mutate(color = replace_na(color, default_color)) %>% 
	mutate(commuters_in = commuters_in/population_model,
				 commuters_out = commuters_out/population_model
	)

# File reading functions --------------------------------------------------------------------
read_state_file <- function(filename) {
	states <- read_csv(filename, col_types = cols(), guess_max = 100000) %>% 
		mutate(I = Ia + Ip + Is) %>% 
		select(!c(Ia,Ip,Is)) %>% 
		pivot_longer(cols = c(S,E,I,R,H,ICU,D), 
								 names_to = "state", 
								 values_to = "count") %>% 
		left_join(municipalities %>% 
								select(municipality, population), 
							by = 'municipality') %>% 
		mutate(municipality = fct_reorder(municipality, population, .desc = TRUE))
	return(states)
}

read_r_file <- function(filename) {
	r <- read_csv(filename, col_types = cols(), guess_max = 100000) %>%
		pivot_longer(
			cols = !c(
				commuter_fraction,
				mutation_chance,
				run,
				strategy,
				prevalence,
				seed,
				day
			),
			names_to = "municipality",
			values_to = "r"
		) %>%
		mutate(seed = replace_na(seed, 'Default')) %>% 
		left_join(municipalities %>% 
								select(municipality, population, color), 
							by = 'municipality') %>% 
		mutate(municipality = fct_reorder(municipality, population, .desc = TRUE))
	return(r)
}

calculate_r_mean <- function(r) {
	r_mean <- r %>%
		filter(day > 15 & day < 45) %>%
		group_by(across(!c(run, day, r))) %>% 
		summarise(r = mean(r, na.rm = TRUE), .groups = 'keep') %>% 
		ungroup()
	return(r_mean)
}
