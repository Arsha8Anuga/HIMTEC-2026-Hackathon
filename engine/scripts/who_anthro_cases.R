# F-03: generate expected z-scores with the official WHO anthro R package.
# Install anthro from the pinned commit used by engine/data/who/README.md:
#   git clone https://github.com/WorldHealthOrganization/anthro.git && cd anthro
#   git checkout b776d8a12b1c97369c748b561159fd2ec4f4db58 && R CMD INSTALL .
# Run from engine/: Rscript scripts/who_anthro_cases.R  (writes tests/data/who_anthro_cases.csv)
# The inputs are synthetic children on the contract's 0.1 cm grid, chosen to cover:
# early infancy, a standing measurement < 731 days (+0.7 cm), a recumbent one >= 731 days
# (-0.7 cm, BB/TB table), and BB/TB beyond +3 SD (restricted LMS) but under the +5 flag.
library(anthro)
cases <- data.frame(
  case = c("bayi_45_hari", "perempuan_300_hari_kurus", "laki_600_hari_berdiri",
           "perempuan_1000_hari_berbaring", "laki_1800_hari_bb_tb_di_atas_3sd"),
  sex = c("male", "female", "male", "female", "male"),
  age_days = c(45, 300, 600, 1000, 1800),
  weight_kg = c(4.5, 6.0, 9.0, 10.5, 22.0),
  length_height_cm = c(55.0, 66.5, 78.0, 85.0, 100.0),
  position = c("recumbent", "recumbent", "standing", "recumbent", "standing"),
  head_circumference_cm = c(38.0, 40.5, 46.0, 47.5, 51.0),
  stringsAsFactors = FALSE
)
z <- anthro_zscores(
  sex = ifelse(cases$sex == "male", 1L, 2L), age = cases$age_days, is_age_in_month = FALSE,
  weight = cases$weight_kg, lenhei = cases$length_height_cm,
  measure = ifelse(cases$position == "recumbent", "l", "h"), headc = cases$head_circumference_cm
)
cases$z_wfa <- z$zwei
cases$z_lhfa <- z$zlen
cases$z_wfl_wfh <- z$zwfl
cases$z_hcfa <- z$zhc
cases$anthro_version <- as.character(packageVersion("anthro"))
write.csv(cases, "tests/data/who_anthro_cases.csv", row.names = FALSE)
print(cases)
