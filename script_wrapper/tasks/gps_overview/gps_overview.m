function gps_overview(username, password, dbname, dburl, KDevice)
% function = GPSvis_database(username, password, KDevice, Colors, STimes, AltChoice, SizeChoice, SpeedClasses)
% KDevices is a vector (length n) with the devices that are included in the anaysis
% Colors is a vector (length n) with the colorsthat are choosen from the list
% STimes is a matrix (nx2)with a vector (length n) with timeStamps of StartTime and a vector (length n) of EndTime
% AltChoice is a vector (length n) with for each device 'clampToGround', 'relativeToGround', 'absolute'
% SpeedClasses is a matrix (nx3) with three threshold values for speed
% SizeChoice is a vector (length n) with 'small', 'medium' , 'large'
% This function uses the Matlab2GoogleEarth toolbox
% clear all
% close all

% display(username);
% display(password);

if ischar(KDevice)
  KDevice = eval(KDevice);
end

display('KDevice');
display(KDevice);
display('DB_PASSWORD');
display(getenv('DB_PASSWORD'));

% dbname = 'flysafe';
% dburl = 'jdbc:postgresql://localhost:5432/flysafe';

conn = database(dbname, username, password, 'org.postgresql.Driver',dburl);
sql1 = 'SELECT device_info_serial, date_time FROM gps.ee_tracker_limited';
results = fetch(conn,sql1);
display(sql1);
display(results)


