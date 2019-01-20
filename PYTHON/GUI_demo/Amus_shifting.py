#AMUSED SPEECH VOICE CONVERSION
#Shifting by percent 
import csv
import scipy.io.wavfile as wav
import pyworld as pw
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import argrelmin
from scipy.signal import argrelmax
import math
import peakutils
import soundfile as sf
import argparse
from audiolazy import *   
from audiolazy.lazy_stream import Stream
from audiolazy import Stream


styletext= '<style>table {width:100%;}table, th, td {border: 1px solid black;border-collapse: collapse;}</style>'


#_y = pw.synthesize(f0, sp, ap, fs)
#if it has less that temporal position pop off the last element
#################################
#DEFINE FORMANT DETECTION FUNCTION 
def cam_formants(x, fs):
	ms10=math.ceil(fs*0.005)
	ms30=math.floor(fs*0.03)
	ncoeff=2+fs/1000
	t = np.arange(0, len(x)-1)
	t = t/fs
	pos = 1
	fm =[]
	ft = []
	while (pos+ms10) <= len(x)+ms10:  #+ms10:
			y=x[pos:pos+ms10-1]
			y=y-np.mean(y)
			a=lpc(y, int(ncoeff))
			a = a.numerator
			rts=np.roots(a)
			rts = [r for r in rts if np.imag(r) >= 0.01]
			ang = np.arctan2(np.imag(rts), np.real(rts))
			frqs = sorted(ang * (fs / (2 * math.pi)))
			frqs = frqs[0:4] #limited to four formants
			#print(frqs[0:4])

			fm.append(frqs)
			ft.append(pos/fs)
			pos = pos+ms10

	return fm,ft


####################################
####################################
def shift_formants(sp, ft, fm, fs, nos_of_peaks, shiftconst_test):
	multi_shiftedarrays = []
	new_sp=[]
	f0_low_limit = 89
	fft_size= 2**math.ceil(np.log2(3 * fs / f0_low_limit + 1))
	frequency_axis=np.arange(0, fft_size+1)/fft_size*fs
	#for each column in fm you want to increanse by the percent and add to the 
	#orginal subtract te diffreneces and add the difference to the 
	#################INCREASE BY SETTING MEAN CONSTANT ###############
	step = fs/fft_size
	#shiftconst_test[:] = [round(x / step) for x in shiftconst_test]
	#################INCREASE BY CONSTANT ###############
	for q in np.arange(0, len(ft)):
		specenv_frame=sp[q,:]
		formant_frame=fm[q]
		test=specenv_frame
		minimas=[i for i in np.arange(1, len(test)-1) if test[i] <= test[i-1]  and test[i]<=test[i+1]]
		#maximas= peakutils.indexes(specenv_frame) 
		maximas = argrelmax(specenv_frame)
		maximas = maximas [0]
		formants_index=[];
		for d in formant_frame: 
		    formants_index.append(np.argmin(abs(frequency_axis-d)))
		new_formants=[];
		if len(maximas) == 0:
			maximass =[formants_index[0]]
		else:
			for k in formants_index:
				new_formants.append(np.argmin(abs(maximas-k)))
				maximass = maximas[np.unique(new_formants)]
		leftValley=[]
		rightValley=[]
		for j in maximass:
			if j <= minimas[0]: #ran into an instance of f1 same as minima[0]
				leftValley.append(0)
			else:  
				leftValley.append(np.amax([i for i in minimas if i < j]))
			if j > minimas[-1]:
				right_v=int(round(j+((len(specenv_frame)-j)/2)))
				rightValley.append(right_v) 
			else:  
				rightValley.append(np.amin([i for i in minimas if i > j]))

		multi_shiftedarrays = []
		mintoloop = min([2, len(maximass)])#ran into an instance where it had more than two maximas ask to choose minimum btwn 2 or len(maxima)
		for k in np.arange(0, mintoloop):#len(maximass)
			peakarray=[]
			peakindex=[]
			for j in np.arange(leftValley[k], rightValley[k]):
				peakarray.append(specenv_frame[j])
				peakindex.append(j)
			shiftconst2= int(round(((formant_frame[k]+(shiftconst_test[k]*0.01*formant_frame[k]))-formant_frame[k])/step))
			shiftconst=shiftconst2
			shifted_array =np.zeros(len(test))
			for i in peakindex:
				shifted_array[i+shiftconst]=test[i]
			if shiftconst<0:
				for k in np.arange(0, abs(shiftconst)):
					shifted_array[peakindex[-1]+k-1]=peakarray[-1]
			else:
				for k in np.arange(0, abs(shiftconst)):
					shifted_array[peakindex[0]+k]=peakarray[0]	

			multi_shiftedarrays.append(shifted_array)

		multi_shiftedarrays= np.max(multi_shiftedarrays,axis=0)
		for g in np.where(multi_shiftedarrays == 0)[0]:
			multi_shiftedarrays[g]=test[g]

		new_sp.append(multi_shiftedarrays)
	new_sp = np.array(new_sp)
	return new_sp


def looptoweb(path,f1perc, f2perc):
	#table is the name of the output html 
	x, fs = sf.read(path)
	f0, t = pw.dio(x, fs, f0_floor=50.0, f0_ceil=600.0)
	sp = pw.cheaptrick(x, f0, t, fs)
	ap = pw.d4c(x, f0, t, fs)
	table_file = open('Amus_shifting.html', 'w')
	table_file.write('<!DOCTYPE html><html>'+styletext+'<body><h1>Audio Files <br>'+ path[-30:] +'</h1><table><tr><th>Form1/Form2</th>')
	for k in np.arange(0, len(f2perc)):
		table_file.write('<th>'+ str(f2perc[k])+'%'+'</th>')
	table_file.write('</tr>')
	for i in np.arange(0, len(f1perc)):
		table_file.write('<tr>')
		table_file.write('<td>'+str(f1perc[i])+'%'+'</td>')
		for j in np.arange(0, len(f2perc)):
			audio_out='testaudio/'+'testsmile' + '_' + str(f1perc[i]) + '_' + str(f2perc[j]) +'.wav'
			fm, ft =cam_formants(x,fs)
			shifted_sp=shift_formants(sp, ft, fm, fs, 2, [f1perc[i],f2perc[j]])
			#print('-------------------------'+[f1perc[i],f2perc[j]]+'----------------------------------------')
			new_y = pw.synthesize(f0[0:len(shifted_sp)], shifted_sp, ap[0:len(shifted_sp)], fs)
			wav.write(audio_out,fs, new_y)
			table_file.write('<td><audio controls>')
			#table_file.write(audio_out)
			table_file.write('<source src= '+'"' +audio_out +'"'+' type="audio/mpeg">')
			table_file.write('</audio></td>')
		table_file.write('</tr>')
	table_file.write('</table>')
	table_file.write('<h3>Original Audio</h3><audio controls><source src= '+'"' +path +'"'+' type="audio/mpeg"></audio><br>')
	table_file.write('</body></html>')
	table_file.close()



#nos_of_peaks = 4
#shiftconst_test = [50, 20, 60, 90]
#fm, ft =cam_formants(x,fs)
#shifted_sp = shift_formants(sp, ft, fm, fs, nos_of_peaks, shiftconst_test)
#f1perc=[10,20,30,40,50]
#f2perc=[13,23,33,43,53]
#zyx = looptoweb(f1perc, f2perc)



