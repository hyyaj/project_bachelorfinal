import os
import json
import pandas as pd
from dateutil import parser

# ---- DEFINE AOIs ----
faces_aoi = {'x1': 583, 'y1': 283, 'x2': 797, 'y2': 766}  # Faces AOI
ai_aoi    = {'x1': 998, 'y1': 283, 'x2': 1330, 'y2': 751}  # AI AOI

# ---- Folder containing all participant folders ----
base_folder = 'E:/all_data'

all_data = []

def in_aoi(x, y, aoi):
    return aoi['x1'] <= x <= aoi['x2'] and aoi['y1'] <= y <= aoi['y2']

def parse_ai_image(val):
    try:
        val_str = str(val)  
        num_str = val_str.split('.')[0]  # remove .jpg
        num = int(num_str)
        return pd.Series({
            'ai_conf': abs(num),
            'ai_advice': 'TRUE' if num < 0 else 'FALSE'
        })
    except Exception as e:
        return pd.Series({
            'ai_conf': None,
            'ai_advice': None
        })


# Iterate through all participants
for participant_folder in os.listdir(base_folder):
    participant_path = os.path.join(base_folder, participant_folder)
    if not os.path.isdir(participant_path):
        continue  

    # csv file and json file in the folder
    csv_file = None
    json_file = None
    for file in os.listdir(participant_path):
        if file.lower().endswith('.csv'):
            csv_file = os.path.join(participant_path, file)
        elif file.lower().startswith('fixture') and file.lower().endswith('.json'):
            json_file = os.path.join(participant_path, file)

    # Skip if csv or fixture file is missing 
    if csv_file is None or json_file is None:
        print(f"Skip {participant_folder}：missing CSV or Fixture JSON")
        continue

    # ---- Load gaze JSON data ----
    with open(json_file, 'r') as f:
        gaze_data_raw = json.load(f)

    # gaze data
    gaze_data = []
    for g in gaze_data_raw:
        try:
            created_at = parser.parse(g['CreatedAt'])
            ts = pd.Timestamp(created_at)
            if ts.tz is not None:
                ts = ts.tz_convert('UTC').tz_localize(None)
            else:
                ts = ts.tz_localize(None)

            g['CreatedAt_dt'] = ts
            g['Formatted'] = {
                'X': g.get('X', 0),
                'Y': g.get('Y', 0),
                'duration': float(g.get('TotalDurationMilliSeconds', 0)),
                'timestamp': g.get('TimeStamp', 0)
            }
            gaze_data.append(g)
        except Exception as e:
            print(f"❌ failure: {g.get('CreatedAt')} -> {e}")
            continue

    # ---- Load CSV ----
    df = pd.read_csv(csv_file)

    # Fix timezone
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.tz_localize(None)

    # remove sequence etc.
    df = df[~df['sender_type'].str.contains('flow', case=False, na=False)]
    df = df[~df['sender_type'].str.contains('canvas.Screen', case=False, na=False)]
    df = df.reset_index(drop=True)

    # Compute ai advice and ai confidence
    df[[ 'ai_conf', 'ai_advice']] = df['ai_image'].apply(parse_ai_image)

    # Assign participant id
    df['participant_id'] = participant_folder

    # Calculate AI literacy scores
    ai_lit_columns = ['socio1', 'socio2', 'socio3', 'socio4', 'tech1', 'tech2', 'tech3', 'tech4']
    df[ai_lit_columns] = df[ai_lit_columns].apply(pd.to_numeric, errors='coerce')
    al_score = df[ai_lit_columns].sum().sum()
    df['al_score'] = al_score

    

    ###
    init_dec_indices = df[df['sender'] == 'initial decision'].index
    init_conf_indices = df[df['sender'] == 'Initial confidence'].index
    final_conf_indices = df[df['sender'] == 'Final confidence'].index
    final_decision_indices = df[df['sender'] == 'final decision'].index

    #  initial decision
    for idx in init_dec_indices:
        init_dec = df.loc[idx, 'initial_decision']
        next_final = final_decision_indices[final_decision_indices > idx]
        if not next_final.empty:
            next_idx = next_final[0]
            df.loc[next_idx, 'initial_decision'] = init_dec

    #  initial confidence
    for idx in init_conf_indices:
        init_conf = df.loc[idx, 'initial_confidence']
        next_final = final_decision_indices[final_decision_indices > idx]
        if not next_final.empty:
            next_idx = next_final[0]
            df.loc[next_idx, 'initial_confidence'] = init_conf

    #  Final confidence 
    for idx in final_conf_indices:
        final_conf = df.loc[idx, 'Final_confidence']
        prev_final = final_decision_indices[final_decision_indices < idx]
        if not prev_final.empty:
            prev_idx = prev_final[-1]  
            df.loc[prev_idx, 'Final_confidence'] = final_conf

    ## add reaction times
    # --- Assign response times (RTs) ---

    # Initialize new RT columns
    df['init_decision_rt'] = None
    df['init_conf_rt'] = None
    df['final_decision_rt'] = None 
    df['final_conf_rt'] = None

    # final decision times
    df.loc[df['sender'] == 'final decision', 'final_decision_rt'] = df['duration']


    #  initial decision rt  
    for idx in init_dec_indices:
        rt = df.loc[idx, 'duration']
        next_final = final_decision_indices[final_decision_indices > idx]
        if not next_final.empty:
            next_idx = next_final[0]
            df.loc[next_idx, 'init_decision_rt'] = rt

    # initial confidence rt  
    for idx in init_conf_indices:
        rt = df.loc[idx, 'duration']
        next_final = final_decision_indices[final_decision_indices > idx]
        if not next_final.empty:
            next_idx = next_final[0]
            df.loc[next_idx, 'init_conf_rt'] = rt

    # final confidence rt 
    for idx in final_conf_indices:
        rt = df.loc[idx, 'duration']
        prev_final = final_decision_indices[final_decision_indices < idx]
        if not prev_final.empty:
            prev_idx = prev_final[-1]
            df.loc[prev_idx, 'final_conf_rt'] = rt





    # organze the data set 
    df = df[df['sender'] == 'final decision'].reset_index(drop=True)

    # trial number for each participant
    df['trial_nr'] = range(1, len(df) + 1)

    df['gaze_data'] = None

    #  Match gaze data with timestamp
    for i in range(len(df) - 1):
        start_time = df.loc[i, 'timestamp']
        end_time = df.loc[i + 1, 'timestamp']
        if pd.isnull(start_time) or pd.isnull(end_time):
            continue

        matched = [
            g['Formatted'] for g in gaze_data
            if start_time <= g['CreatedAt_dt'] < end_time
        ]
        df.at[i, 'gaze_data'] = matched if matched else None

    #  Handle gaze data for the last decision (use a 5-second window)
    last_idx = len(df) - 1
    last_start = df.loc[last_idx, 'timestamp']
    last_end = last_start + pd.Timedelta(seconds=5)
    last_matched = [
        g['Formatted'] for g in gaze_data
        if last_start <= g['CreatedAt_dt'] < last_end
    ]
    df.at[last_idx, 'gaze_data'] = last_matched if last_matched else None

    #  Calculate duration on each
    df['AOI_faces'] = 0.0
    df['AOI_AI'] = 0.0
    df['Total_duration'] = 0.0

    for i, row in df.iterrows():
        gaze_points = row['gaze_data'] or []
        faces_time = 0.0
        ai_time = 0.0
        total_time = 0.0
        for g in gaze_points:
            x, y, dur = g['X'], g['Y'], g['duration']
            total_time += dur
            if in_aoi(x, y, faces_aoi):
                faces_time += dur
            if in_aoi(x, y, ai_aoi):
                ai_time += dur

        df.at[i, 'AOI_faces'] = faces_time
        df.at[i, 'AOI_AI'] = ai_time
        df.at[i, 'Total_duration'] = total_time

    
    # Keep only desired columns in the final DataFrame
    df = df[['sender',
             'timestamp',
             'final_decision',
             'initial_decision',
             'true_value',
             'ai_conf',
             'ai_advice',
             'gaze_data',
             'AOI_faces',
             'AOI_AI',
             'Total_duration',
             'participant_id',
             'al_score', 
             'trial_nr',
             'initial_confidence',
             'Final_confidence',
             'init_decision_rt',
             'init_conf_rt',
             'final_decision_rt',
             'final_conf_rt']]


    all_data.append(df)

#  Combine and export all data
final_df = pd.concat(all_data, ignore_index=True)

#  
final_df.to_excel('all_data10.xlsx', index=False)

print("All data are combined! ")
