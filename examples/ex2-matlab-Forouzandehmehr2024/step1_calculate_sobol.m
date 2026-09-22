%% OUTPUT OF INTEREST
M = readtable('_sobol_results/simulation_manifest.csv', 'Delimiter', ',');
T = readtable('_sobol_results/biomarkers.csv', 'Delimiter', ',')
%% Select output for Sobol analysis

% analysisType = 'NaNcount';
analysisType = 'APD90';
% analysisType = 'APD50';
% analysisType = 'APD30';

if strcmp(analysisType,'APD30')

    Y = T.APD30_ms_;

elseif strcmp(analysisType,'APD50')

    Y = T.APD50_ms_;

elseif strcmp(analysisType,'APD90')

    Y = T.APD90_ms_;

elseif strcmp(analysisType,'NaNcount')

    Y = double(isnan(T.APD90_ms_));

else

    error('Unknown analysisType')

end

%% PARAMETERS
parNames = [ ...
    "g_Kr"
    "gNa"
    "kNaCa"];

d = numel(parNames);
names = string(M.Var1);
%% A and B samples

idxA = startsWith(names,"A_") & ~startsWith(names,"A_B_");
idxB = startsWith(names,"B_");

YA = Y(idxA);
YB = Y(idxB);

N = numel(YA);

fprintf("A samples: %d\n",N);
fprintf("B samples: %d\n",numel(YB));

if numel(YB) ~= N
    error("A and B sample counts differ");
end

%% AB samples

YAB = nan(N,d);

for p = 1:d

    idx = startsWith(names,"A_B_" + parNames(p) + "_");

    tmp = Y(idx);

    if numel(tmp) ~= N
        error("%s contains %d samples, expected %d", ...
            parNames(p), numel(tmp), N);
    end

    YAB(:,p) = tmp(:);
end
%% Remove rows containing NaNs

% valid = ~isnan(YA) & ~isnan(YB);

% for p = 1:d
    % valid = valid & ~isnan(YAB(:,p));
% end

YA(isnan(YA)) = 0;
YB(isnan(YB)) = 0;
YAB(isnan(YAB)) = 0;
% YA  = YA(valid);
% YB  = YB(valid);
% YAB = YAB(valid,:);

fprintf("Valid samples after NaN removal: %d\n",numel(YA));

%% Variance

VY = var([YA;YB],1);

%% Sobol indices

S1 = nan(d,1);
ST = nan(d,1);

for p = 1:d

    yab = YAB(:,p);

    % Saltelli first-order index
    S1(p) = mean(YB .* (yab - YA)) / VY;

    % Jansen total-order index
    ST(p) = mean((YA - yab).^2) / (2*VY);

end

%% Results
names = ["I_K_r","I_N_a","I_N_C_x"];

% Custom colors (RGB)
colors = [
    0.45 0.70 0.45   % green
    0.40 0.60 0.85   % blue
    0.85 0.40 0.40   % red
];

figure

t = tiledlayout(1,2,'TileSpacing','compact','Padding','compact');

%% S1
ax1 = nexttile;
h1 = pie(ax1,S1*1000);
title(ax1,'S_1')
axis(ax1,'equal')

patches1 = findobj(ax1,'Type','Patch');
for k = 1:length(patches1)
    patches1(k).FaceColor = colors(end-k+1,:);
end

%% ST
ax2 = nexttile;
h2 = pie(ax2,ST*1000);
title(ax2,'S_T')
axis(ax2,'equal')

patches2 = findobj(ax2,'Type','Patch');
for k = 1:length(patches2)
    patches2(k).FaceColor = colors(end-k+1,:);
end

% Make absolutely sure both pies use same scaling
xlim(ax1,[-1.2 1.2]); ylim(ax1,[-1.2 1.2]);
xlim(ax2,[-1.2 1.2]); ylim(ax2,[-1.2 1.2]);

% Common legend
lgd = legend(patches1(end:-1:1), names, ...
    'Orientation','horizontal');
lgd.Layout.Tile = 'south';
lgd.FontSize = 16;
