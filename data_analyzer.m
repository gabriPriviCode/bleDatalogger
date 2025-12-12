close all
clear
clc 

filename_temp = '1_sensor_data.csv';
filename_rh = '2_sensor_data.csv';

try
    table_1 = readtable(filename_temp);
    time_data = table_1{:, "Time"};
    temperature_data = table_1{:, "TempC"};
    temperature_reference = table_1{:, "TempRef"};

    time = zeros(length(time_data));
    for i = 1 : length(time)
        time(i) = 10 * i;
    end

    ref_temp_values = temperature_reference;
    temp_steps = [1; find(abs(diff(ref_temp_values)) > 0); length(ref_temp_values)];
    temp_intervals = [];
    temp_means = [];
    temp_std = [];
    temp_incA = [];

    for k = 1:length(temp_steps)-1
        idx1 = temp_steps(k);
        idx2 = temp_steps(k+1);
        
        vals = temperature_data(idx1:idx2);
        
        interval_mean = mean(vals);
        interval_std = std(vals);
        interval_incA = interval_std / sqrt(length(vals));
        
        temp_intervals = [temp_intervals; temperature_reference(idx1)];
        temp_means = [temp_means; interval_mean];
        temp_std = [temp_std; interval_std];
        temp_incA = [temp_incA; interval_incA];
    end

    figure()
    title('Temperature plot');
    plot(time, temperature_data);
    hold on;
    plot(time, temperature_reference);
    xlabel('Time (s)');
    ylabel('Temperature (°C)');
    legend("Measured temperature", "Temperature Reference");
    grid on

    figure()
    error = temperature_reference - temperature_data;
    max_std = max(temp_std);
    errorbar(temp_intervals(2:8), temp_means(1:7), temp_incA(1:7), '-o');
    hold on;
    upper_line = temp_intervals(2:8) + 3 * max_std;
    lower_line = temp_intervals(2:8) - 3* max_std;
    plot(temp_intervals(2:8), temp_intervals(2:8), '--');
    hold on;
    plot(temp_intervals(2:8), upper_line);
    hold on;
    plot(temp_intervals(2:8), lower_line);
    xlabel('Temperature (°C)');
    ylabel('Temperature (°C)');
    legend('Sensor temperature', 'Chamber temperature', 'Chamber temperature + 3 * STD', 'Chamber temperature - 3 * STD')
    grid on
    
    table_2 = readtable(filename_rh);
    time_data = table_2{:, "Time"};
    rh_data = table_2{:, "HumRH"};
    rh_reference = table_2{:, "HumRef"};

    time = zeros(length(time_data));
    for i = 1 : length(time)
        time(i) = 10 * i;
    end

    ref_rh_values = rh_reference;
    rh_steps = [1; find(abs(diff(ref_rh_values)) > 0); length(ref_rh_values)];
    rh_intervals = [];
    rh_means = [];
    rh_std = [];
    rh_incA = [];

    for k = 1:length(rh_steps)-1
        idx1 = rh_steps(k);
        idx2 = rh_steps(k+1);

        vals = rh_data(idx1:idx2);

        interval_mean = mean(rh_data(idx1:idx2));
        interval_std = std(rh_data(idx1:idx2));
        rh_intervals = [rh_intervals; rh_reference(idx1)];
        interval_incA = interval_std / sqrt(length(vals));
        rh_means = [rh_means; interval_mean];
        rh_std = [rh_std; interval_std];
        rh_incA = [rh_incA ; interval_incA];
    end

    figure()
    title('Relative Humidity plot');
    plot(time, rh_data);
    hold on;
    plot(time, rh_reference);
    xlabel('Time (s)');
    ylabel('Relative Humidity (%)');
    legend("Measured humidity", "Humidity Reference");
    grid on


    figure()
    error = rh_reference - rh_data;
    max_std = max(rh_std);
    errorbar(rh_intervals(2:11), rh_means(1:10), rh_incA(1:10), '-o');
    hold on;
    upper_line = rh_intervals(2:11) + 3 * max_std;
    lower_line = rh_intervals(2:11) - 3 * max_std;
    plot(rh_intervals(2:11), rh_intervals(2:11), '--');
    hold on;
    plot(rh_intervals(2:11), upper_line);
    hold on;
    plot(rh_intervals(2:11), lower_line);
    xlabel('Relative Humidity (%)');
    ylabel('Relative Humidity (%)');
    legend('Sensor humidity', 'Chamber humidity', 'Chamber humidity + 3 * STD', 'Chamber humidity - 3 * STD');
    grid on

    temp_results = table(temp_intervals, temp_means, temp_std, ...
    'VariableNames', {'ReferenceValue', 'MeanValue', 'StdDev'});

    rh_results = table(rh_intervals, rh_means, rh_std, ...
    'VariableNames', {'ReferenceValue', 'MeanValue', 'StdDev'});


catch Exception
    fprintf("The following exception occurred: %s", Exception.message)
    return
end
