clean_up_beer_style <- function(beer_style_name){
  if (beer_style_name == "IPA - Imperial / Double New England / Hazy"){
    return ("Double New England IPA")
  } else if (beer_style_name == "Red Ale - American Amber / Red"){
    return ("Red American Amber")
  } else if (beer_style_name %in% c("IPA - New England / Hazy", "IPA - New England")){
    return ("New England IPA")
  } else if (beer_style_name == "IPA - Imperial / Double"){
    return ("Double IPA")
  } else if (beer_style_name == "Farmhouse Ale - Saison"){
    return ("Farmhouse Ale")
  } else if (beer_style_name == "Stout - Imperial / Double"){
    return ("Imperial Stout")
  } else if (beer_style_name == "Sour - Fruited Gose"){
    return ("Sour - Fruited")
  }
  
  return (beer_style_name)
}
