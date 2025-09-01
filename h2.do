import excel "E:\all_data10.xlsx", firstrow clear

// Some preparations: 
// convert values to 0 or 1
// same=true=1; different=false=0
gen byte ai_advice_bin = .
replace ai_advice_bin = 1 if ai_advice == "TRUE"
replace ai_advice_bin = 0 if ai_advice == "FALSE"

gen byte true_value_bin = true_value

gen byte initial_bin = .
replace initial_bin = 1 if initial_decision == "same"
replace initial_bin = 0 if initial_decision == "different"

gen byte final_bin = .
replace final_bin = 1 if final_decision == "same"
replace final_bin = 0 if final_decision == "different"

// create dummy variables
gen disagreement = (initial_bin != ai_advice_bin)
gen switch_to_ai = (initial_bin != ai_advice_bin) & (final_bin == ai_advice_bin) 
gen ai_correct = (ai_advice_bin == true_value_bin)

//////////////////////////////////////////////////////////////////
drop if participant_id == "C10_P5" //no data for this participant
drop if Total_duration == 0 //no connection with eyetracker during the trial
//////////////////////////////////////////////////////////
egen mean_al = mean(al_score)
gen al_score_c = al_score - mean_al

egen mean_conf = mean(ai_conf)
gen ai_conf_c = ai_conf - mean_conf
/////////////////////////////////////

encode participant_id, gen(pid_num)

xtset pid_num

xtlogit switch_to_ai c.ai_conf_c##c.al_score_c initial_confidence if disagreement == 1, re //h2a

xtreg AOI_faces c.ai_conf_c##c.al_score_c initial_confidence if disagreement == 1, re  //h2b

//gen fixation_ratio = AOI_faces / (AOI_faces + AOI_AI)

//xtreg fixation_ratio c.ai_conf##c.al_score if disagreement == 1, re

/*check outliers
predict yhat if e(sample), xb
gen resid = AOI_faces - yhat if e(sample)
summarize resid if e(sample)
gen resid_std = (resid - r(mean)) / r(sd) if e(sample)

//2. list observations with standardized residuals greater than 3
list pid_num resid resid_std if abs(resid_std) > 3 & e(sample)

// 3. excluding potential outliers (standardized residuals > 3)
xtreg AOI_faces c.ai_conf##c.al_score if disagreement == 1 & abs(resid_std) <= 3, re


