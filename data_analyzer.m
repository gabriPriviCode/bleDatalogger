close all
clear
clc 

filename = 'sensor_data.csv';

try
    table = readtable(filename);
    time_data = table{:, "Time"};
    temperature_data = table{:, "TempC"};
    rh_data = table{:, "HumRH"};

    figure()
    title('Temperature plot');
    plot(time_data, temperature_data);
    xlabel('Time (hh/mm/ss)');
    ylabel('Temperature (°C)');

    figure()
    title('Relative Humidity plot');
    plot(time_data, rh_data);
    xlabel('Time (hh/mm/ss)');
    ylabel('Relative Humidity (%)');

catch Exception
    fprintf("The following exception occurred: %s", Exception.message)
    return
end