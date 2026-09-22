%% Load Vm_all, and time_all
if ~exist('Vm_all')
    baseDir = '_population';

    d = dir(baseDir);
    d = d([d.isdir]); % keep only directories
    d = d(~ismember({d.name}, {'.', '..'})); % remove . and ..
    [~, idx] = sort({d.name});
    d = d(idx);
    time_all = cell(numel(d), 1);
    Vm_all   = cell(numel(d), 1);

    for k = 1:numel(d)
        matFile = fullfile(baseDir, d(k).name, 'res.mat');
    
        if isfile(matFile)
            S = load(matFile, 'time', 'Vm');

            time_all{k} = S.time;
            Vm_all{k}   = S.Vm;
        else
            warning('File not found: %s', matFile);
        end
    end
end
%% Load curve profiles
% if ~exist('types')
    f = {'_population/healthy.csv', '_population/lqt.csv'};
    types = cell(size(f));
    for k = 1:numel(f)
        lines = readlines(f{k});
        nums = cellfun(@(x) ...
                       str2double(regexp(x, '\d+', 'match', 'once')), ...
                       cellstr(lines));
        types{k} = nums;
    end
% end

%% plot
figure(3);

line_colors = {[0.2 0.7 0.1 0.2], [0.7 0.2 0.1 0.2] };
for i = 1:numel(time_all)
    t = time_all{i};
    v = Vm_all{i};

    % Find peaks
    [~, locs] = findpeaks(v, t);

    if numel(locs) < 5
        warning('Trace %d has fewer than 5 peaks. Skipping.', i);
        continue
    end

    % 5th peak from the end
    t_peak = locs(end-4);

    % Align time
    t_aligned = t - t_peak;

    % Align plot
    idx = (t_aligned >= -0.2) & (t_aligned <= 1);
    gray = 1;

    for j = 1:numel(types)
        if sum(types{j} == i) > 0
            color = line_colors{j};
            gray = 0;
            break;
        end
    end

    if gray
        p = plot(t_aligned(idx), v(idx) * 1000, 'Color', [0.25, 0.25, 0.25, 0.1]);
    else
        p = plot(t_aligned(idx), v(idx) * 1000, 'Color', color);
    end
    hold on
end

xlabel('Time (s)')
ylabel('Vm (mV)')
hold off
