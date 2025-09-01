/////new h1
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
gen ai_correct = (ai_advice_bin == true_value_bin)

gen ai_incorrect = (ai_correct == 0)
gen human_final_correct = (final_bin == true_value_bin)
gen human_final_wrong = (human_final_correct == 0)

///////////////////////////////////////////
// Over-Reliance numerator and denominator (only when disagreement)
gen over_case_disagree = (disagreement == 1 & ai_incorrect == 1 & human_final_wrong == 1)
gen ai_incorrect_disagree = (disagreement == 1 & ai_incorrect == 1)

// Under-Reliance numerator and denominator (only when disagreement)
gen under_case_disagree = (disagreement == 1 & ai_correct == 1 & human_final_wrong == 1)
gen ai_correct_disagree = (disagreement == 1 & ai_correct == 1)

////
// check descriptive stats
//gen total_disagree = (disagreement == 1)
//collapse (sum) ///
 //   ai_correct_disagree ///
   // under_case_disagree ///
 //   ai_incorrect_disagree ///
//    over_case_disagree ///
  //  total_disagree, by(participant_id)
	
//list participant_id ///
 //    ai_correct_disagree ///
  //   under_case_disagree ///
 //    ai_incorrect_disagree ///
 //    over_case_disagree ///
  //   total_disagree


///////////
collapse (sum) over_case_disagree ai_incorrect_disagree ///
             under_case_disagree ai_correct_disagree (first) al_score, by(participant_id)


// Calculate final ratios
gen over_reliance_ratio = over_case_disagree / ai_incorrect_disagree
gen under_reliance_ratio = under_case_disagree / ai_correct_disagree

///////////
scatter over_reliance_ratio al_score ||lfit over_reliance_ratio al_score, ///
xtitle("AI Literacy") ytitle("Over-reliance Ratio")
scatter under_reliance_ratio al_score ||lfit under_reliance_ratio al_score, ///
xtitle("AI Literacy") ytitle("Under-reliance Ratio") 

spearman over_reliance_ratio al_score
spearman under_reliance_ratio al_score

reg over_reliance_ratio c.al_score, robust
reg under_reliance_ratio c.al_score, robust

graph box over_reliance_ratio, ///
    title("Over-Reliance Ratio") ///
    ytitle("Ratio") ///
    ylabel(0(0.2)1)

graph box under_reliance_ratio, ///
    title("Under-Reliance Ratio") ///
    ytitle("Ratio") ///
    ylabel(0(0.2)1)


// 
//list participant_id over_reliance_ratio under_reliance_ratio
//scatter over_reliance_ratio al_score ||lfit over_reliance_ratio al_score 
//scatter under_reliance_ratio al_score ||lfit under_reliance_ratio al_score 

//pwcorr over_reliance_ratio al_score, sig
//pwcorr under_reliance_ratio al_score, sig

