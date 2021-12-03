plot_missing <- function(data, percent=F, shortenNames=F) {
  require(tidyverse)
  require(patchwork)
  
  
  missing_patterns <- data.frame(is.na(data)) %>%
    group_by_all() %>%
    count(name = "count", sort = TRUE) %>%
    ungroup()
    
  plots_input <- missing_patterns %>% 
    rownames_to_column(var="id") %>% 
    mutate(id=factor(as.integer(id)))
  
  # Create the input for the hist for missing values by variable
  input_variable_hist <- plots_input %>%
    gather(key, value, -c(id, count)) %>%
    group_by(key) %>%
    summarise(variable_count = sum(count * value)) %>%
    arrange(desc(variable_count)) %>%
    mutate(variable_order=row_number())
  
  pivot_missing_patterns <- plots_input %>%
    gather(key, value, -c(id, count)) %>%
    inner_join(input_variable_hist, "key") %>%
    mutate(id = factor(id)) %>%
    mutate(key = fct_reorder(key, variable_order, min))

  missing_id <- pivot_missing_patterns %>%
    group_by(id) %>%
    summarise(n_of_missing = sum(value)) %>%
    filter(n_of_missing == 0) %>%
    pull(id)

  x_levels <- levels(pivot_missing_patterns$key)
  missing_id_x <- x_levels[ceiling((length(x_levels)) / 2)]
  missing_id_y <- levels(missing_id)[missing_id]
  missing_id_y <- ifelse(is_empty(missing_id_y), -1, missing_id_y)

  pivot_missing_patterns <- pivot_missing_patterns %>%
    mutate(value = ifelse(id == missing_id_y, "Complete", ifelse(value, "Missing", "Not missing"))) %>%
    mutate(value = factor(value, levels = c("Missing", "Not missing", "Complete")))

  ## visualize missing value pattern
  p_tile <- ggplot(pivot_missing_patterns, aes(x = key, y = fct_rev(id), fill = value)) +
    geom_tile(color = "white") +
    scale_fill_manual(values=c("Missing" = "#B69FE5",
                               "Not missing" = "#CBCBCB", 
                               "Complete" = "#B3B3B3")) +
    xlab("Variable")  +
    ylab("Missing Pattern") +
    theme(legend.title = element_blank()) +
    theme(legend.position = "none") +
    annotate("text", x = missing_id_x, y = missing_id_y, label = "Complete Case")
  
  # Short the x-axis labels if the the flag is enabled
  if (shortenNames){
    p_tile <- p_tile + scale_x_discrete(labels = abbreviate)
  }
  
  # Overwrite variable_count with percentage if perecent is T
  if (percent){
    input_variable_hist$variable_count = input_variable_hist$variable_count / nrow(data)
  }
  
  # Create the histogram
  p_variable_hist <- ggplot(input_variable_hist, aes(x=fct_reorder(key, variable_order), y=variable_count)) + 
    geom_bar(stat = "identity", fill="#97B7F1") +
    xlab(element_blank()) +
    ylab("number rows missing") +
    theme_bw() +
    theme(
      panel.grid.major.x = element_blank() ,
      panel.grid.major.y = element_line( size=.1, color="gray")
    )
  
  # Short the x-axis labels if the the flag is enabled
  if (shortenNames){
    p_variable_hist <- p_variable_hist + scale_x_discrete(labels = abbreviate)
  }
  
  if (percent){
    p_variable_hist <- p_variable_hist +
      ylab("% rows missing") +
      scale_y_continuous(labels = scales::percent_format(accuracy = 1L, suffix=""), limits = c(0, 1.0))
  }
  
  # Create the input for the hist for missing patterns
  input_pattern_hist <- plots_input %>%
    select(c(id, count)) %>%
    mutate(is_complete=ifelse(id == missing_id_y, "Complete", "Missing"))
  
  # Overwrite variable_count with percentage if perecent is T
  if (percent){
    input_pattern_hist$count = input_pattern_hist$count / nrow(data)
  }

  p_pattern_hist <- ggplot(input_pattern_hist, 
                           aes(x=fct_rev(id), y=count, fill = is_complete)) + 
    geom_bar(stat = "identity") + 
    scale_fill_manual(values = c(
      "Missing" = "#97B7F1",
      "Complete" = "#6495EC")) +
    coord_flip() +
    xlab(element_blank())  +
    ylab("row count") + 
    theme_bw() + 
    theme(
      panel.grid.major.y = element_blank(),
      legend.title = element_blank(),
      legend.position = "none"
    )

  if (percent){
    p_pattern_hist <- p_pattern_hist +
      ylab("% rows") +
      scale_y_continuous(labels = scales::percent_format(accuracy = 1L, suffix=""), limits = c(0, 1.0))
  }

  p_variable_hist + plot_spacer() + p_tile + p_pattern_hist + plot_layout(widths = c(4, 1), heights = c(2, 8))
}
