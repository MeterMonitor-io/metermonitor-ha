import sqlite3
from datetime import datetime

def correct_value(db_file:str, name: str, new_eval, allow_negative_correction = False, max_flow_rate = 1.0):
    # get last evaluation
    reject = False
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        segments = len(new_eval[2])
        # get last history entry
        cursor.execute("SELECT value, timestamp, confidence FROM history WHERE name = ? ORDER BY ROWID DESC LIMIT 2", (name,))
        rows = cursor.fetchall()
        if len(rows) == 0:
            conn.commit()
            return None
        row = rows[0]

        second_row = rows[1] if len(rows) > 1 else None

        last_value = str(row[0]).zfill(segments)
        last_time = datetime.fromisoformat(row[1])
        last_confidence = row[2]
        try:
            new_time = datetime.fromisoformat(new_eval[3])
        except Exception as e:
            print(f"[CorrectionAlg ({name})] Error parsing new evaluation time (assuming current): {e}")
            new_time = datetime.now()

        new_results = new_eval[2]
        denied_digits = new_eval[4]

        if last_time >= new_time:
            print(f"[CorrectionAlg ({name})] Time difference to last message is negative, assuming current time for correction")
            new_time = datetime.now()

        max_flow_rate /= 60.0
        # get the time difference in minutes
        time_diff = (new_time - last_time).seconds / 60.0


        correctedValue = ""
        totalConfidence = 1.0
        # used confidence tracks the confidence of digits that actually are being funneled into the correction
        usedConfidence = 1.0
        negative_corrected = False
        for i, lastChar in enumerate(last_value):

            predictions = new_results[i]
            digit_appended = False
            for prediction in predictions:

                tempValue = correctedValue
                tempConfidence = totalConfidence

                # replacement of the rotation class
                if prediction[0] == 'r' or denied_digits[i]:
                    # check if the digit before has changed upwards, set the digit to 0
                    if i > 0 and int(correctedValue[-1]) > int(last_value[i-1]):
                        tempValue += '0'
                        tempConfidence *= prediction[1]
                    else:
                        tempValue += lastChar
                        tempConfidence *= prediction[1]
                else:
                    tempValue += prediction[0]
                    tempConfidence *= prediction[1]

                # check if the new value is higher than the last value (positive flow)
                if int(tempValue) >= int(last_value[:i+1]) or negative_corrected and tempConfidence > 0.15:
                    correctedValue = tempValue
                    totalConfidence = tempConfidence
                    if not denied_digits[i]: usedConfidence *= prediction[1]
                    digit_appended = True
                    break

                # check conditions for negative correction
                elif allow_negative_correction:
                    if second_row:
                        pre_last_value = str(second_row[0]).zfill(segments)
                        # if last history entry has a very low confidence, but current confidence is high enough
                        # compare with the second last entry
                        if last_confidence < 0.2 and tempConfidence > 0.50 and \
                                int(tempValue) >= int(pre_last_value[:i+1]):
                            correctedValue = tempValue
                            totalConfidence = tempConfidence
                            usedConfidence *= prediction[1]
                            digit_appended = True
                            negative_corrected = True
                            print(f"[CorrectionAlg ({name})] Negative correction accepted")
                            break

            # if no digit was appended, append the original digit but reject the value
            if not digit_appended:
                correctedValue += lastChar
                reject = True
                print(f"[CorrectionAlg ({name})] Fallback: appending original digit", lastChar)

        # get the flow rate and check if it is within the limits
        flow_rate = (int(correctedValue) - int(last_value)) / 1000.0 / time_diff
        if flow_rate > max_flow_rate or (flow_rate < 0 and not allow_negative_correction) or reject:
            print(f"[CorrectionAlg ({name})] Flow rate is too high or negative")
            return None
        
        print (f"[CorrectionAlg ({name})] Value accepted for time", new_time, "flow rate", flow_rate, "value", correctedValue)
        return int(correctedValue), totalConfidence, usedConfidence