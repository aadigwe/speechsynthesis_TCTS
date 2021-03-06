function new_spectrogram= shiftwholewaveform_frame(data,raw, shift1_const, shift2_const,frequency_axis)

%DATA: THE SPECTRUM_PARAMETER.SPECTROGRAM 
time_array=raw(:,1);

formants_freq =[];
formants_pos=[];
for j=raw(:,2)'
        [M,I] = min(abs(frequency_axis-j));
        formants_freq=[formants_freq; frequency_axis(I)];
        formants_pos=[formants_pos; I];
end 

formants2_freq =[];
formants2_pos=[];
for k=raw(:,3)'
        [M,I] = min(abs(frequency_axis-k));
        formants2_freq=[formants2_freq; frequency_axis(I)];
        formants2_pos=[formants2_pos; I];
end 

%3. LOCALISE VALLEYS FOR EACH FORMNAT 1 & 2 AND SHFT PEAK FILL AND REMOVE

new_spectrogram=[];
for i = 1:length(shift1_const)
        spec_env=data(:,i);
        [peakarray]=localise_valley(spec_env,formants_pos(i), spec_env(formants_pos(i)));
        [peakarray2]=localise_valley(spec_env,formants2_pos(i), spec_env(formants2_pos(i)));
        [shifted_array]= shiftpeaks2(spec_env, peakarray,shift1_const(i),peakarray2,shift2_const(i));
        [newarray]= fill_remove(spec_env,shifted_array,peakarray(2,:),peakarray2(2,:),shift1_const(i),shift2_const(i));
        new_spectrogram= [new_spectrogram,newarray'];
end 

