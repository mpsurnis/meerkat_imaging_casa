# meerkat_imaging_casa
Standalone python scripts to carry out quick imaging with MeerKAT data
This is a standalone version of the oxkat pipeline hosted at https://github.com/IanHeywood/oxkat and derives all the procedures from it.

The initial set-ups are pretty self-explanatory. There are some important variables. They are explained below:

doselfcal (default: True) : This sets whether the user wants to do a phase self-cal or not

dotimeslices (default: True) : This sets if the time slice images are needed or just full integration image is fine.

time_before, time_on, time_after : Time ranges for the imaging of an FRB for localization.

imspw : The channel range to image over. Useful for sources detected in part of band.
