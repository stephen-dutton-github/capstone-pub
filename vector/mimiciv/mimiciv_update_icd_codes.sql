INSERT INTO d_icd_diagnoses (icd_code,icd_version,long_title) VALUES ('J1282',10,'Pneumonia due to COVID-19');

-- Enfoce subset rules for patients
-- Remove all records with seq_num > 1
DELETE FROM diagnoses_icd WHERE seq_num > 1;

-- Set icd_code = 'J159' and icd_version = 10 for the first 25 subject_ids (pneumonia)
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10040025;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10039997;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10039831;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10039708;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10038999;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10038992;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10038933;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10038081;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10037975;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10037928;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10037861;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10036156;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10035631;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10035185;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10032725;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10031757;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10031404;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10029484;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10029291;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10027602;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10027445;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10026406;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10026354;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10026255;
UPDATE diagnoses_icd SET icd_code = 'J159', icd_version = 10 WHERE subject_id = 10025612;

-- Set icd_code = 'A19' and icd_version = 10 for the next 25 subject_ids (Tuberculosis)
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10025463;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10024043;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10023771;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10023239;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10023117;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10022880;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10022281;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10022041;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10022017;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10021938;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10021666;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10021487;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10021312;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10021118;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020944;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020786;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020740;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020640;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020306;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10020187;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10019917;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10019777;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10019568;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10019385;
UPDATE diagnoses_icd SET icd_code = 'A19', icd_version = 10 WHERE subject_id = 10019172;

-- Set icd_code = 'J1282' and icd_version = 10 for the next 25 subject_ids (Covid)
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10019003;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10018845;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10018501;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10018423;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10018328;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10018081;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10017492;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10016810;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10016742;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10016150;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10015931;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10015860;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10015272;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10014729;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10014354;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10014078;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10013049;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10012853;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10012552;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10011398;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10010867;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10010471;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10009628;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10009049;
UPDATE diagnoses_icd SET icd_code = 'J1282', icd_version = 10 WHERE subject_id = 10009035;