SET PYTHON="C:\Python27\python.exe"
SET SOURCE="C:\Users\psautosend\SFTP_Root\edline"
SET OUTPUT="C:\ProgramData\Livelink\Kentfield_School_District\Data\GenericUploads"

DEL %OUTPUT%\*.csv
CD "\Users\psautosend\Documents\GitHub\ps_engage"
%PYTHON% engage_sync.py --autosend --source_dir=%SOURCE% --output_dir=%OUTPUT%
