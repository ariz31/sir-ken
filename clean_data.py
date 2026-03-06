import pandas as pd
import re

def clean_location(loc):
    if pd.isna(loc):
        return "Unknown"
    loc = str(loc).strip().title()
    # Handle multiple spaces
    loc = re.sub(r'\s+', ' ', loc)
    return loc

def clean_data():
    input_file = "Questionnaire - Sheet1 (4).csv"
    output_file = "cleaned_dataset.csv"

    # Read original data
    df = pd.read_csv(input_file)
    print(f"Original dataset shape: {df.shape}")

    # 1. Remove duplicates (ignoring Timestamp)
    # We keep the first submission and drop subsequent identical submissions
    duplicates = df.drop(columns=['Timestamp']).duplicated(keep='first')
    num_dups = duplicates.sum()
    df = df[~duplicates]
    print(f"Removed {num_dups} duplicate rows.")

    # 2. Handle missing values
    # ReasonForNoBIM is legitimately null for most
    df['ReasonForNoBIM'] = df['ReasonForNoBIM'].fillna("N/A")
    # Location
    df['Location'] = df['Location'].fillna("Unknown")

    # 3. Clean logic errors
    # Age - YearsOfExperience < 15 is illogical
    logic_mask = (df['Age'] - df['YearsOfExperience']) >= 15
    num_illogical = (~logic_mask).sum()
    df = df[logic_mask]
    print(f"Removed {num_illogical} rows with illogical Age/YearsOfExperience.")

    # 4. Clean text columns
    df['Location'] = df['Location'].apply(clean_location)

    # Ensure likert scale columns are strictly within 1-5
    adv_cols = [c for c in df.columns if c.startswith('adv_')]
    chal_cols = [c for c in df.columns if c.startswith('chal_')]
    strat_cols = [c for c in df.columns if c.startswith('strat_')]
    all_likert = adv_cols + chal_cols + strat_cols

    # Check if there are any values outside 1-5 and filter them out just in case
    # (Though we checked earlier and there were none)
    likert_mask = df[all_likert].apply(lambda x: x.between(1, 5)).all(axis=1)
    num_invalid_likert = (~likert_mask).sum()
    df = df[likert_mask]
    if num_invalid_likert > 0:
        print(f"Removed {num_invalid_likert} rows with invalid Likert scale values.")

    # 5. Remove low quality responses (straight-liners)
    # Calculate the standard deviation across all 55 Likert scale items.
    # If the standard deviation is 0, the respondent provided the exact same
    # answer for every single question (e.g. all 3s, all 4s, all 5s). This is
    # indicative of low effort and not actually reading the questions.
    likert_std = df[all_likert].std(axis=1)
    straight_liners_mask = likert_std == 0
    num_straight_liners = straight_liners_mask.sum()
    df = df[~straight_liners_mask]
    print(f"Removed {num_straight_liners} low quality straight-liner responses (std == 0).")

    # Save the cleaned dataset
    df.to_csv(output_file, index=False)
    print(f"Cleaned dataset saved to {output_file}. New shape: {df.shape}")

if __name__ == "__main__":
    clean_data()
