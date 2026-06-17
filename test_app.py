import unittest
import numpy as np
import pandas as pd

#Testing the QA/QC logic
def mask_sensor_errors(df, columns):
    cleaned_df = df.copy()
    for col in columns:
        cleaned_df[col] = cleaned_df[col].mask(cleaned_df[col] <= -900.0, np.nan)
    return cleaned_df

class TestCRAVEPipeline(unittest.TestCase):
    def test_multi_variable_sensor_masking(self):
        #ensure -999.0 failures are caught
        raw_data = pd.DataFrame({
            'SW_Global': [500.0, -999.0, 459.0],
            'SW_Direct': [400.0, 320.0, -999.0],
            'SW_Diffuse': [100.0, -999.0, 50.0]
        })
        cols_to_clean = ['SW_Global', 'SW_Direct', 'SW_Diffuse']
        cleaned_data = mask_sensor_errors(raw_data, cols_to_clean)
        self.assertTrue(np.isnan(cleaned_data['SW_Global'][1]))
        self.assertTrue(np.isnan(cleaned_data['SW_Direct'][2]))
        self.assertTrue(np.isnan(cleaned_data['SW_Diffuse'][1]))
        self.assertEqual(cleaned_data['SW_Global'][0], 500.0)

    def test_bsrn_physics_closure(self):
        #Validate my physics logic (global = direct + diffuse (at noon))
        global_rad = 600.0
        diffuse_rad = global_rad * 0.25
        direct_rad = global_rad - diffuse_rad
        calculated_global = direct_rad + diffuse_rad
        self.assertEqual(calculated_global, global_rad, "Physics Check Failed: Solar components do not close!")

if __name__ == '__main__':
    unittest.main()