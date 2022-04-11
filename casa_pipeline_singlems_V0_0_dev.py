# Pipeline for analysing imaging data from the MeerKAT telescope
# Based on the oxkat pipeline hosted here: https://github.com/IanHeywood/oxkat
# 15 March 2022
# Contact msurnis@gmail.com in case of any issues
# Started compiling the first scratch pipeline
# This pipeline assumes that the calibrator and target are in different MS files
#################################Set Defaults###################################
# Initial config set-up (The target, calibrator names can be obtained using litobs) 

import shutil
myms = 'FRB19_cut.ms'
target_ms = 'FRB19_calib.ms'
bpcal_name = 'J0408-6545'
bpcal = bpcal_name
pcal_name = 'J1311-2216'
pcal = pcal_name
refant = 'm001'
ref_ant = refant
gapfill = 24
myuvrange = '>150m'
delaycut = 2.5
target = 'J1337-28'
ktab0 = myms+'_'+'tt'+'.K0'
bptab0 = myms+'_'+'tt'+'.B0'
gtab0 = myms+'_'+'tt'+'.G0'
ktab1 = myms+'_'+'tt'+'.K1'
bptab1 = myms+'_'+'tt'+'.B1'
gtab1 = myms+'_'+'tt'+'.G1'
ktab2 = myms+'_'+'tt'+'.K2'
gtab2 = myms+'_'+'tt'+'.G2'
ftab2 = myms+'_'+'tt'+'.flux2'
ktab3 = myms+'_'+'tt'+'.K3'
gtab3 = myms+'_'+'tt'+'.G3'
ftab3 = myms+'_'+'tt'+'.flux3'

# ------------------------------------------------------------------------

# Begin the actual data analysis

# ------------------------------------------------------------------------

# Basic flagging step

# ------------------------------------------------------------------------
# Frequency ranges to flag over all baselines

badfreqs = ['850~900MHz', # Lower band edge
	'1658~1800MHz', # Upper bandpass edge
	'1419.8~1421.3MHz'] # Galactic HI

myspw = ''
for badfreq in badfreqs:
	myspw += '*:'+badfreq+','
myspw = myspw.rstrip(',')

flagdata(vis = myms,mode = 'manual',spw = myspw)


# ------------------------------------------------------------------------
# Frequency ranges to flag over a subset of baselines
# From the MeerKAT Cookbook
# https://github.com/ska-sa/MeerKAT-Cookbook/blob/master/casa/L-band%20RFI%20frequency%20flagging.ipynb

badfreqs = ['900MHz~915MHz', # GSM and aviation
	'925MHz~960MHz',				
	'1080MHz~1095MHz',
	'1565MHz~1585MHz', # GPS
	'1217MHz~1237MHz',
	'1375MHz~1387MHz',
	'1166MHz~1186MHz',
	'1592MHz~1610MHz', # GLONASS
	'1242MHz~1249MHz',
	'1191MHz~1217MHz', # Galileo
	'1260MHz~1300MHz',
	'1453MHz~1490MHz', # Afristar
	'1616MHz~1626MHz', # Iridium
	'1526MHz~1554MHz', # Inmarsat
	'1600MHz'] # Alkantpan

myspw = ''
for badfreq in badfreqs:
	myspw += '*:'+badfreq+','
myspw = myspw.rstrip(',')

flagdata(vis = myms,mode = 'manual',spw = myspw,uvrange = '<600')


# ------------------------------------------------------------------------
# Clipping, quacking, zeros, autos
# Note that clip will always flag NaN/Inf values even with a range 

flagdata(vis = myms,mode = 'manual',autocorr = True)

flagdata(vis = myms,mode = 'clip',clipzeros = True)

flagdata(vis = myms,mode = 'clip',clipminmax = [0.0,100.0])

# ------------------------------------------------------------------------
# Save the flags

flagmanager(vis = myms,mode = 'save',versionname = 'basic')

# ------------------------------------------------------------------------

# setjy and initial flagging step

# ------------------------------------------------------------------------

if bpcal == 'J1939-6342':
   setjy(vis=myms,field=bpcal_name,standard='Stevens-Reynolds 2016',scalebychan=True,usescratch=True)
        
elif bpcal == 'J0408-6545':
     bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
     setjy(vis=myms,field=bpcal_name,standard='manual',fluxdensity=bpcal_mod[0],spix=bpcal_mod[1],reffreq=bpcal_mod[2],scalebychan=True,usescratch=True)

# ------------------------------------------------------------------------

# bpcal flagging
flagdata(vis=myms,mode='rflag',datacolumn='data',field=bpcal)
flagdata(vis=myms,mode='tfcrop',datacolumn='data',field=bpcal)
flagdata(vis=myms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=bpcal)

# pcal flagging
flagdata(vis=myms,mode='rflag',datacolumn='data',field=pcal)
flagdata(vis=myms,mode='tfcrop',datacolumn='data',field=pcal)
flagdata(vis=myms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=pcal)

# ------------------------------------------------------------------------

# Gain calibration step

# ------------------------------------------------------------------------

# --------------------------------------------------------------- #
# --------------------------- STAGE 0 --------------------------- #
# --------------------------------------------------------------- #

# ------- K0 (primary)

gaincal(vis=myms,field=bpcal,caltable=ktab0,refant = str(ref_ant),gaintype = 'K',solint = 'inf',parang=False)

# ------- G0 (primary; apply K0)

gaincal(vis=myms,field=bpcal,uvrange=myuvrange,caltable=gtab0,gaintype='G',solint='inf',calmode='p',minsnr=5,gainfield=[bpcal],interp = ['nearest'],gaintable=[ktab0])

# ------- B0 (primary; apply K0, G0)

bandpass(vis=myms,field=bpcal,uvrange=myuvrange,caltable=bptab0,refant = str(ref_ant),solint='inf',combine='',solnorm=False,minblperant=4,minsnr=3.0,bandtype='B',fillgaps=gapfill,parang=False,gainfield=[bpcal,bpcal],interp = ['nearest','nearest'],gaintable=[ktab0,gtab0])

flagdata(vis=bptab0,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab0,mode='rflag',datacolumn='CPARAM')

# ------- Correct primary data with K0,B0,G0

applycal(vis=myms,gaintable=[ktab0,gtab0,bptab0],field=bpcal,parang=False,gainfield=[bpcal,bpcal,bpcal],interp = ['nearest','nearest','nearest'])

# ------- Flag primary on CORRECTED_DATA - MODEL_DATA

flagdata(vis=myms,mode='rflag',datacolumn='residual',field=bpcal)
flagdata(vis=myms,mode='tfcrop',datacolumn='residual',field=bpcal)
flagmanager(vis=myms,mode='save',versionname='bpcal_residual_flags')

# --------------------------------------------------------------- #
# --------------------------- STAGE 1 --------------------------- #
# --------------------------------------------------------------- #

# ------- K1 (primary; apply B0, G0)

gaincal(vis=myms,field=bpcal,caltable=ktab1,refant = str(ref_ant),gaintype = 'K',solint = 'inf',parang=False,gaintable=[bptab0,gtab0],gainfield=[bpcal,bpcal],interp=['nearest','nearest'])

# ------- G1 (primary; apply K1,B0)

gaincal(vis=myms,field=bpcal,uvrange=myuvrange,caltable=gtab1,gaintype='G',solint='inf',calmode='p',minsnr=5,gainfield=[bpcal,bpcal],interp = ['nearest','nearest'],gaintable=[ktab1,bptab0])

# ------- B1 (primary; apply K1, G1)

bandpass(vis=myms,field=bpcal,uvrange=myuvrange,caltable=bptab1,refant = str(ref_ant),solint='inf',combine='',solnorm=False,minblperant=4,minsnr=3.0,bandtype='B',fillgaps=gapfill,parang=False,gainfield=[bpcal,bpcal],interp = ['nearest','nearest'],gaintable=[ktab1,gtab1])

flagdata(vis=bptab1,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab1,mode='rflag',datacolumn='CPARAM')

# ------- Correct primary data with K1,G1,B1

applycal(vis=myms,gaintable=[ktab1,gtab1,bptab1],field=bpcal,parang=False,gainfield=[bpcal,bpcal,bpcal],interp = ['nearest','nearest','nearest'])

# --------------------------------------------------------------- #
# --------------------------- STAGE 2 --------------------------- #
# --------------------------------------------------------------- #

# ------- G2 (primary; a&p sols per scan / SPW)

gaincal(vis = myms,field = bpcal,uvrange = myuvrange,caltable = gtab2,refant = str(ref_ant),solint = 'inf',solnorm = False,combine = '',minsnr = 3,calmode = 'ap',parang = False,gaintable = [ktab1,gtab1,bptab1],gainfield = [bpcal,bpcal,bpcal],interp = ['nearest','nearest','nearest'],append = False)

# ------- Duplicate K1
# ------- Duplicate G2 (to save repetition of above step)

shutil.copytree(ktab1,ktab2)
shutil.copytree(gtab2,gtab3)

# --- G2 (secondary) 

gaincal(vis = myms,field = pcal,uvrange = myuvrange,caltable = gtab2,refant = str(ref_ant),minblperant = 4,minsnr = 3,solint = 'inf',solnorm = False,gaintype = 'G',combine = '',calmode = 'ap',parang = False,gaintable=[ktab1,gtab1,bptab1],gainfield=[bpcal,bpcal,bpcal],interp=['nearest','linear','linear'],append=True)

# --- K2 (secondary)

gaincal(vis = myms,field = pcal,caltable = ktab1,refant = str(ref_ant),gaintype = 'K',solint = 'inf',parang = False,gaintable = [gtab1,bptab1,gtab2],gainfield = [bpcal,bpcal,pcal],interp = ['nearest','linear','linear','linear'],append = True)

# --- Correct secondary with K2, G1, B1, G2

applycal(vis = myms,gaintable = [ktab2,gtab1,bptab1,gtab2],field = pcal,parang = False,gainfield = ['','',bpcal,pcal],interp = ['nearest','linear','linear','linear'])

# --- Flag secondary on CORRECTED_DATA - MODEL_DATA

flagdata(vis = myms,field = pcal,mode = 'rflag',datacolumn = 'residual')
flagdata(vis = myms,field = pcal,mode = 'tfcrop',datacolumn = 'residual')
flagmanager(vis=myms,mode='save',versionname='pcal_residual_flags')

# --------------------------------------------------------------- #
# --------------------------- STAGE 3 --------------------------- #
# --------------------------------------------------------------- #

gaincal(vis=myms,field=bpcal,uvrange=myuvrange,caltable=gtab3,refant=str(ref_ant),solint='inf',solnorm=False,combine='',minsnr=3,calmode='ap',parang=False,gaintable=[ktab2,gtab1,bptab1],gainfield=[bpcal,bpcal,bpcal],interp=['nearest','nearest','nearest'],append=False)

# ------- Duplicate K1 table

shutil.copytree(ktab1,ktab3)

# --- G3 (secondary)

gaincal(vis=myms,field=pcal,uvrange=myuvrange,caltable=gtab3,refant=str(ref_ant),minblperant=4,minsnr=3,solint='inf',solnorm=False,gaintype='G',combine='',calmode='ap',parang=False,gaintable=[ktab2,gtab1,bptab1],gainfield=[bpcal,bpcal,bpcal],interp=['nearest','linear','linear'],append=True)

# --- K3 secondary

gaincal(vis=myms,field=pcal,caltable=ktab3,refant=str(ref_ant),gaintype='K',solint='inf',parang=False,gaintable=[gtab1,bptab1,gtab3],gainfield=[bpcal,bpcal,bpcal,pcal],interp=['linear','linear','linear'],append=True)

# --- Correct secondaries with K3, G1, B1, G3

applycal(vis=myms,gaintable=[ktab3,gtab1,bptab1,gtab3],field=pcal,parang=False,gainfield=['','',bpcal,pcal],interp=['nearest','linear','linear','linear'])

# ------- Apply final tables to targets
# --- Correct targets with K3, G1, B1, G3

applycal(vis=myms,gaintable=[ktab3,gtab1,bptab1,gtab3],field=target,parang=False,gainfield=['',bpcal,bpcal,pcal],interp=['nearest','linear','linear','linear'])
flagmanager(vis=myms,mode='save',versionname='refcal-full')

# ------------------------------------------------------------------------

# Cut out the target and imaging step

# ------------------------------------------------------------------------

mstransform(vis=myms,outputvis=target_ms,field=target,usewtspectrum=True,realmodelcol=True,datacolumn='corrected')

# --- RFI flagging on the calibrated target data

flagdata(vis=target_ms,mode='rflag',datacolumn='data',field=target)
flagdata(vis=target_ms,mode='tfcrop',datacolumn='data',field=target)
flagdata(vis=target_ms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=target)

# --- First form the full integration image

full_integ_imagename = target + '_full'
tclean(vis=target_ms,selectdata=True,field="",spw="",timerange="",uvrange="",antenna="",scan="",observation="",intent="",datacolumn="corrected",imagename=full_integ_imagename,imsize=[5000, 5000],cell=['3.0arcsec'],phasecenter="",stokes="I",projection="SIN",startmodel="",specmode="mfs",reffreq="",nchan=-1,start="",width="",outframe="LSRK",veltype="radio",restfreq=[],interpolation="linear",perchanweightdensity=True,gridder="widefield",facets=1,psfphasecenter="",chanchunks=1,wprojplanes=-1,vptable="",mosweight=True,aterm=True,psterm=False,wbawp=False,conjbeams=False,cfcache="",usepointing=False,computepastep=360.0,rotatepastep=360.0,pointingoffsetsigdev=[],pblimit=-1,normtype="flatnoise",deconvolver="mtmfs",scales=[0, 5, 15],nterms=2,smallscalebias=0.6,restoration=True,restoringbeam=[],pbcor=False,outlierfile="",weighting="briggs",robust=0,noise="1.0Jy",npixels=0,uvtaper=[],niter=25000,gain=0.1,threshold="0.05mJy",nsigma=0.0,cycleniter=-1,cyclefactor=0.5,minpsffraction=0.05,maxpsffraction=0.8,interactive=False,usemask="auto-multithresh",mask="",pbmask=0.0,sidelobethreshold=2.5,noisethreshold=5.0,lownoisethreshold=1.5,negativethreshold=0.0,smoothfactor=1.0,minbeamfrac=0.3,cutthreshold=0.01,growiterations=75,dogrowprune=True,minpercentchange=-1.0,verbose=False,fastnoise=True,restart=True,savemodel="modelcolumn",calcres=True,calcpsf=True,parallel=False)
