# Plot the COM data over time.

##########################################################################################

# Plotting function
save_plot <- function(filepath,filename,data_plot) {
	png(paste(filepath,filename,".png",sep=""), width=7, height=5.25, units="in", res=300)
	print(data_plot)
	dev.off()
	
	pdf(paste(filepath,filename,".pdf",sep=""), width=7, height=5.25)
	print(data_plot)
	dev.off()
}

# Calculate the stance phases for an individual.
stance_versus_flight <- function(data_com,data_touch,low_time,upp_time,num_gaps) {
	time_filtered_sub_com_data <- subset(data_com,Time > low_time & Time < upp_time)
	time_filtered_touch_data <- subset(data_touch, Time > low_time & Time < upp_time)
	
	# Find the stance phases of touching.
	# 1) Get the unique times for touching. (Include starting and ending times.)
	# 2) Find the largest X number of gaps (Dependent on each case and the time interval.)
	# 3) Establish critical points to form the boxes.
	# 4) Get the minimum num_gaps - 1 to form your boxes.
	# 5) Get the x positions for the critical points.
	
	# 1)
	un_times <- sort(unique(time_filtered_touch_data$Time))
	un_times <- c(low_time,un_times,upp_time)
	un_times
	
	# 2)
	time_gaps <- diff(un_times)
	time_gaps
	ordered_gaps <- order(time_gaps,decreasing=TRUE) # Get the vector indices for the maximum gaps in time_gaps.  Largest are listed first.
	
	# 3) Index of the gap is the index and the index + 1 in the timeline.
	cp <- c()
	for (i in 1:num_gaps) {
		gap <- ordered_gaps[i]
		cp <- c(cp,un_times[gap])
		cp <- c(cp,un_times[gap+1])
	}
	cp <- sort(cp)
	cp
	
	# 4)
	cp_gaps <- diff(cp)
	ordered_gaps <- order(cp_gaps)
	cps <- data.frame(time_low_bound=c(),time_upp_bound=c(),X_low_bound=c(),X_upp_bound=c())
	for (i in 1:(num_gaps-1)) {
		gap <- ordered_gaps[i]
		cps <- rbind(cps,data.frame(time_low_bound=cp[gap],time_upp_bound=cp[gap+1],X_low_bound=c(0),X_upp_bound=c(0)))
	}
	cps
	
	# 5)
	for (i in 1:length(cps[,1])) {
		subset(time_filtered_touch_data, Time == cps[i,1])
		cps[i,3] <- min(subset(time_filtered_touch_data, Time == cps[i,1])$X)
		cps[i,4] <- max(subset(time_filtered_touch_data, Time == cps[i,2])$X)
	}
	cps <- na.omit(cps)
	return(cps)
}

##########################################################################################

# Setup the basic file structure for reading data.

# Test case for single use.
base_path <- "/Users/JMoore/Desktop/"
com_data_full_path <- paste(base_path,"Testing_MOI_Analysis_composite_com_data.dat",sep="")
ang_mom_full_path <- paste(base_path,"Testing_MOI_Analysis_angular_mom_data.dat",sep="")

# Production code for different experiments.
base_path <- "/Users/JMoore/Documents/Publications/hopping_journal/Experiments/"
exp_path <- c(
	"straight_tail_hopper/", #1
	"evo_straight_actuated_tail/", #2
	"straight_angled_tail_hopper/", #3
	"evo_angled_straight_actuated_tail/", #4
	"evo_tail_fixed_mass_straight_actuated_tail_0_3_per_seg_mass/", #5
	"evo_tail_fixed_mass_straight_actuated_tail_0_6_per_seg_mass/", #6
	"evo_tail_fixed_mass_straight_actuated_tail_0_15_per_seg_mass/", #7
	"evo_angled_curved_actuated_tail/", #8
	"ankle_fix/evo_tail_fixed_mass_straight_actuated_tail_0_9_total_mass/",  #9
	"ankle_fix/evo_tail_fixed_mass_straight_actuated_tail_0_6_total_mass/", #10
	"ankle_fix/evo_tail_fixed_mass_straight_actuated_tail_0_3_total_mass/", #11
	"ankle_fix/mass_runs/evo_tail_fixed_mass_straight_actuated_tail_0_9_total_mass/", #12
	"ankle_fix/mass_runs/evo_tail_fixed_mass_straight_actuated_tail_0_6_total_mass/", #13
	"ankle_fix/mass_runs/evo_tail_fixed_mass_straight_actuated_tail_0_3_total_mass/" #14
		)
sec_path <- "validator_logging/"

ang_mom_file <- "ang_mom_data/DEAP_Hopper_RUN_Gen_GEN_Ind_0_angular_mom_data.dat"
com_data_file <- "com_data/DEAP_Hopper_RUN_Gen_GEN_Ind_0_composite_com_data.dat"
ref_point_file <- "ref_point_data/DEAP_Hopper_RUN_Gen_GEN_Ind_0_reference_point_data.dat"
touch_file <- "contact_sensors/DEAP_Hopper_RUN_Gen_GEN_Ind_0__contacts.dat"
touch_file <- "body_touching/DEAP_Hopper_RUN_Gen_GEN_Ind_0__body_touches.dat"

exp_num <- 14
run_num <- 13
gen <- 1999

# Construct the full paths for the data.
ang_mom_full_path <- gsub("RUN",run_num,ang_mom_file)
ang_mom_full_path <- gsub("GEN",gen,ang_mom_full_path)
ang_mom_full_path <- paste(base_path,exp_path[exp_num],run_num,"/",sec_path,ang_mom_full_path,sep="")

com_data_full_path <- gsub("RUN",run_num,com_data_file)
com_data_full_path <- gsub("GEN",gen,com_data_full_path)
com_data_full_path <- paste(base_path,exp_path[exp_num],run_num,"/",sec_path,com_data_full_path,sep="") 

ref_point_full_path <- gsub("RUN",run_num,ref_point_file)
ref_point_full_path <- gsub("GEN",gen,ref_point_full_path)
ref_point_full_path <- paste(base_path,exp_path[exp_num],run_num,"/",sec_path,ref_point_full_path,sep="") 

touch_full_path <- gsub("RUN",run_num,touch_file)
touch_full_path <- gsub("GEN",gen,touch_full_path)
touch_full_path <- paste(base_path,exp_path[exp_num],run_num,"/",sec_path,touch_full_path,sep="")

##########################################################################################

# Read in the center of mass data.
com_data <- read.csv(com_data_full_path,head=TRUE,sep=",")
#com_data <- subset(com_data, Body != 'left_leg')
summary(com_data)

# Read in the Reference Point Data
ref_point_data <- read.csv(ref_point_full_path,head=TRUE,sep=",")
ref_point_data$Body <- as.factor("ref_point")
ref_point_data$COM_X <- ref_point_data$Ref_Point_X
ref_point_data$COM_Y <- ref_point_data$Ref_Point_Y
drops <- c("Ref_Point_X","Ref_Point_Y","Ref_Point_Z")
ref_point_data <- ref_point_data[,!(names(ref_point_data) %in% drops)]
ref_point_data$Mass <- NA
summary(ref_point_data)

# Read in the touch data.
touch_data <- read.csv(touch_full_path,head=TRUE,sep=",")
touch_data$Body_ID <- as.factor(touch_data$Body_ID)
touch_data$Body <- as.factor("NA")
touch_data$Touched <- 1 # Need to demarcate that a contact was made at this point.
summary(touch_data)

# Link the body numbers to the limbs.
touch_data$Body <- as.factor(touch_data$Body_ID)
levels(touch_data$Body)[levels(touch_data$Body)==0]   <- "Rear Segment"
levels(touch_data$Body)[levels(touch_data$Body)==1]   <- "Mid Segment"
levels(touch_data$Body)[levels(touch_data$Body)==2]   <- "Front Segment"
levels(touch_data$Body)[levels(touch_data$Body)==3]   <- "Left Rear Upper"
levels(touch_data$Body)[levels(touch_data$Body)==4]   <- "Right Rear Upper"
levels(touch_data$Body)[levels(touch_data$Body)==5]   <- "Left Rear Mid"
levels(touch_data$Body)[levels(touch_data$Body)==6]   <- "Right Rear Mid"
levels(touch_data$Body)[levels(touch_data$Body)==7]   <- "Left Rear Low"
levels(touch_data$Body)[levels(touch_data$Body)==8]   <- "Right Rear Low"
levels(touch_data$Body)[levels(touch_data$Body)==9]   <- "Left Rear Foot"
levels(touch_data$Body)[levels(touch_data$Body)==10]  <- "Right Rear Foot"
levels(touch_data$Body)[levels(touch_data$Body)==11]  <- "Left Front Upper"
levels(touch_data$Body)[levels(touch_data$Body)==12]  <- "Right Front Upper"
levels(touch_data$Body)[levels(touch_data$Body)==13]  <- "Left Front Foot"
levels(touch_data$Body)[levels(touch_data$Body)==14]  <- "Right Front Foot"
levels(touch_data$Body)[levels(touch_data$Body)==15]  <- "Tail Front"
levels(touch_data$Body)[levels(touch_data$Body)==16]  <- "Tail Mid"
levels(touch_data$Body)[levels(touch_data$Body)==17]  <- "Tail Rear"
levels(touch_data$Body)[levels(touch_data$Body)==18]  <- "Head"
summary(touch_data)

# Read in the angular momentum data.
ang_mom_data <- read.csv(ang_mom_full_path,head=TRUE,sep=",")
#ang_mom_data <- subset(ang_mom_data, Body != 'left_leg')
summary(ang_mom_data)

##########################################################################################

unified_data <- rbind(com_data,ref_point_data)
summary(unified_data)

mod_val <- 0.3

tail_com_data  <- subset(unified_data, Body == 'tail'      & (Time %% mod_val <= abs(0.001) | Time %% mod_val >= abs(mod_val-0.01)))
leg_com_data   <- subset(unified_data, Body == 'both_rear_legs' & (Time %% mod_val <= abs(0.001) | Time %% mod_val >= abs(mod_val-0.01)))
torso_com_data <- subset(unified_data, Body == 'torso'     & (Time %% mod_val <= abs(0.001) | Time %% mod_val >= abs(mod_val-0.01)))
ref_point_data <- subset(unified_data, Body == 'ref_point' & (Time %% mod_val <= abs(0.001) | Time %% mod_val >= abs(mod_val-0.01)))

sub_com_data <- rbind(tail_com_data,leg_com_data)
sub_com_data <- rbind(sub_com_data,torso_com_data)
sub_com_data <- rbind(sub_com_data,ref_point_data)
summary(sub_com_data)

# Plot the Y Position of the COM over time.
plt <- ggplot(unified_data, aes(x=Time,y=COM_Y)) +
	labs(title="Center of Mass Over Time",x="Time",y="COM Height") +
	theme(legend.position="bottom") +
	xlim(min=0,max=10) +
	ylim(min=0,max=2) +
	geom_line(data=torso_com_data,aes(x=Time,y=COM_Y,color="Torso"),alpha=0.3,size=1,linetype=2) +
	geom_line(data=leg_com_data,aes(x=Time,y=COM_Y,color="Leg"),alpha=0.3,size=1,linetype=2) +
	geom_line(data=tail_com_data,aes(x=Time,y=COM_Y,color="Tail"),alpha=0.3,size=1,linetype=2) +	
	geom_line(data=ref_point_data,aes(x=Time,y=COM_Y,color="Ref Point"),alpha=1.0,size=1.5) +	
	scale_color_manual(name="Points",values=c(cbPalette[6],cbPalette[1],cbPalette[7],cbPalette[8]),breaks=c("Ref Point","Torso","Leg","Tail"))
plt

# Normalize to the reference point.
sub_com_data$Norm_Height <- ifelse(sub_com_data$Body == "ref_point",0.0,sub_com_data$COM_Y-subset(sub_com_data,Time == sub_com_data$Time & sub_com_data$Body == "ref_point")$COM_Y)

# Plot the normalized Y Position of the COM over time.
plt <- ggplot(sub_com_data, aes(x=Time,y=Norm_Height)) +
	labs(title="Center of Mass Over Time",x="Time",y="COM Height") +
	theme(legend.position="bottom") +
	xlim(min=0,max=10) +
	ylim(min=-1,max=1) +
	geom_line(data=subset(sub_com_data, Body == "torso"),aes(color="Torso"),alpha=0.8,size=1,linetype=1) +
	geom_line(data=subset(sub_com_data, Body == "both_rear_legs"),aes(color="Leg"),alpha=0.8,size=1,linetype=1) +
	geom_line(data=subset(sub_com_data, Body == "tail"),aes(color="Tail"),alpha=0.8,size=1,linetype=1) +	
	geom_line(data=subset(sub_com_data, Body == "ref_point"),aes(color="Ref Point"),alpha=1.0,size=1.5) +	
	scale_color_manual(name="Points",values=c(cbPalette[6],cbPalette[1],cbPalette[7],cbPalette[8]),breaks=c("Ref Point","Torso","Leg","Tail"))
plt

save_plot(base_path,"normalized_com_over_time",plt)

# Add in the flight phases if we have them.
plt <- ggplot() +
	labs(title="Center of Mass Over Time",x="Time",y="COM Height") +
	theme(legend.position="bottom") +
	#xlim(min=low_bound,max=upp_bound) +
	ylim(min=0,max=3.5) +
	geom_rect(data=cps,aes(xmin=time_low_bound,ymin=0,xmax=time_upp_bound,ymax=3.5),color="black",alpha=0.4,group=NA)  +
	geom_line(data=torso_com_data,aes(x=Time,y=COM_Y,color="Torso"),alpha=0.9,size=1,linetype=2) +
	geom_line(data=leg_com_data,aes(x=Time,y=COM_Y,color="Leg"),alpha=0.9,size=1,linetype=2) +
	geom_line(data=tail_com_data,aes(x=Time,y=COM_Y,color="Tail"),alpha=0.9,size=1,linetype=2) +	
	geom_line(data=ref_point_data,aes(x=Time,y=COM_Y,color="Ref Point"),alpha=1.0,size=1.5) +	
	scale_color_manual(name="Points",values=c(cbPalette[6],"black",cbPalette[7],cbPalette[8]),breaks=c("Ref Point","Torso","Leg","Tail"))
plt

save_plot(base_path,"com_y_over_time",plt)

# Plot the COM Data
low_time_bound <- 4
upp_time_bound <- 7

sub_time_filtered_data <- subset(sub_com_data, Time < upp_time_bound & Time > low_time_bound)
summary(sub_time_filtered_data)

plt <- ggplot() +
	labs(title="Center of Mass Movement",x="X Position",y="Y Position") +
	theme(legend.position="bottom") +
#	xlim(min=-4,max=90) +
	ylim(min=0,max=4) +
	geom_rect(data=cps,aes(xmin=X_low_bound,ymin=0,xmax=X_upp_bound,ymax=4),color="black",alpha=0.4,group=NA)  +
	geom_line(data=subset(sub_time_filtered_data, Body != 'tail' & Body != 'torso' & Time > low_time_bound & Time < upp_time_bound),aes(x=COM_X,y=COM_Y,group=Time),color="black") +
	geom_line(data=subset(sub_time_filtered_data, Body != 'both_rear_legs' & Body != 'tail' & Time > low_time_bound & Time < upp_time_bound),aes(x=COM_X,y=COM_Y,group=Time),color="black") +	
	geom_line(data=subset(sub_time_filtered_data, Body != 'both_rear_legs' & Body != 'torso' & Time > low_time_bound & Time < upp_time_bound),aes(x=COM_X,y=COM_Y,group=Time),color="black") +	
	geom_point(data=sub_time_filtered_data,aes(x=COM_X,y=COM_Y,group=Body,shape=Body,fill=Body),color="black",size=3) +
	geom_point(data=time_filtered_td, aes(x=X,y=0),color="black")  +
	scale_fill_manual(values=c(cbPalette[6],cbPalette[5],cbPalette[7],cbPalette[8])) +
	scale_shape_manual(values=c(21,22,23,24)) +
	coord_fixed()
plt

save_plot(base_path,"com_over_time",plt)

##############################################################################################################################
        
# Very simple plot showing when the bodies contact the ground.
touch_data$Mod_Touched <- touch_data$Touched - 0.1 + 0.01 * as.integer(touch_data$Body_ID)
plt <- ggplot(touch_data, aes(x=Time, y=Mod_Touched, color=Body)) +
	geom_point(aes(shape=Body),size=4) +
	scale_shape_manual(values=c(0,1,2,16,17,18,19,20))
plt

save_plot(base_path,"touching_information",plt)

##############################################################################################################################

low_time_bound <- 4.0
upp_time_bound <- 6.0
cps <- stance_versus_flight(subset(sub_com_data,Time > low_time_bound & Time < upp_time_bound),subset(touch_data, Time > low_time_bound & Time < upp_time_bound),low_time_bound,upp_time_bound,3)
cps

time_filtered_sub_com_data <- sub_time_filtered_data
time_filtered_touch_data <- subset(touch_data, Time < upp_time_bound & Time > low_time_bound)
time_filtered_d <- subset(time_filtered_sub_com_data, Time > low_time_bound & Time < upp_time_bound)
time_filtered_td <- subset(time_filtered_touch_data, Time > low_time_bound & Time < upp_time_bound)

#plt <- ggplot(time_filtered_sub_com_data, aes(x=COM_X,group=Body,color=Body,y=COM_Y)) +
plt <- ggplot() +
	labs(title="Center of Mass Movement",x="X Position",y="Y Position") +
	theme(legend.position="bottom") +
#	xlim(min=-2,max=60) +
#	ylim(min=0,max=4) +
	geom_rect(data=cps,aes(xmin=X_low_bound,ymin=0,xmax=X_upp_bound,ymax=4),color="black",alpha=0.4,group=NA)  +
	geom_line(data=subset(sub_time_filtered_data, Body != 'tail' & Body != 'torso'),aes(group=Time,x=COM_X,y=COM_Y),color="black") +
	geom_line(data=subset(sub_time_filtered_data, Body != 'both_rear_legs' & Body != 'tail'),aes(group=Time,x=COM_X,y=COM_Y),color="black") +	
	geom_line(data=subset(sub_time_filtered_data, Body != 'both_rear_legs' & Body != 'torso'),aes(group=Time,x=COM_X,y=COM_Y),color="black") +	
	geom_point(data=sub_time_filtered_data, aes(x=COM_X,group=Body,color=Body,y=COM_Y,shape=Body,fill=Body),color="black",size=3) +
	geom_point(data=time_filtered_td, aes(x=X,y=0),color="black")  +
	scale_fill_manual(values=c(cbPalette[6],cbPalette[5],cbPalette[7],cbPalette[8])) +
	scale_shape_manual(values=c(21,22,23,24)) +
	coord_fixed()
plt

save_plot(base_path,"COM_per_groups_over_time",plt)

##############################################################################################################################

aggregate_data <- subset(ang_mom_data,Body == 'both_rear_legs')$Ang_Mom + subset(ang_mom_data,Body == 'tail')$Ang_Mom + subset(ang_mom_data,Body == 'torso')$Ang_Mom
summary(aggregate_data)

derived_ang_mom_data <- data.frame(time=unique(ang_mom_data$Time), aggregate=aggregate_data)
summary(derived_ang_mom_data)

library(pspline)
qplot(derived_ang_mom_data$time,predict(sm.spline(derived_ang_mom_data$time, subset(ang_mom_data,Body == 'both_rear_legs')$Ang_Mom), derived_ang_mom_data$time, 1))

plt <- ggplot(derived_ang_mom_data, aes(x=time,y=aggregate)) +
	geom_line() +
	geom_point(data=touch_data, aes(x=Time,y=0),color="black")  +
	ylim(min=-5,max=5)
plt

# Get the flight/stance phases for the entire simulation.
full_cps <- stance_versus_flight(com_data,touch_data,0.0,10.0,20)
# Replace any infinite values with 0 (occurs for start.)
full_cps <- do.call(data.frame,lapply(full_cps, function(x) replace(x, is.infinite(x),0.0)))
full_cps

# Plot the angular momentum data with touch information included.
plt <- ggplot() +
	labs(title="Sum Angular Momentum",x="Time",y="Angular Momentum") +
	#geom_line(derived_ang_mom_data, aes(x=time,y=aggregate)) +
	geom_point(data=touch_data, aes(x=Time,y=0),color="black")  +
	geom_rect(data=full_cps,aes(xmin=time_low_bound,ymin=-1.0,xmax=time_upp_bound,ymax=1.0),color="black",alpha=0.4) +
	geom_line(data=derived_ang_mom_data, aes(x=time,y=aggregate)) +
	ylim(min=-5.0,max=5.0)
plt

save_plot(base_path,"sum_ang_mom_over_time_w_touching",plt)

# Plot the ang_mom data over time.
# Transform the ang_mom_data for torso.
summary(ang_mom_data)
ang_mom_data$norm_ang_mom <- ifelse(ang_mom_data$Body == "torso" | ang_mom_data$Body == "tail",ang_mom_data$Ang_Mom/10.0,ang_mom_data$Ang_Mom)

plt <- ggplot() +
	labs(title="Angular Momentum Over Time",x="Time",y="Angular Momentum") +
	theme(legend.position="bottom") +
	ylim(min=-1.2,max=1.2) +
	xlim(min=4.0,max=9.0) +
	#geom_rect(data=full_cps,aes(xmin=time_low_bound,ymin=-0.025,xmax=time_upp_bound,ymax=0.025),color="black",alpha=0.4) +	
	geom_point(data=subset(ang_mom_data,Body == 'both_rear_legs' | Body == 'torso' | Body == 'tail'), aes(x=Time,y=norm_ang_mom,group=Body,shape=Body,fill=Body),color="black",size=3,alpha=0.4) +
	scale_fill_manual(values=c(cbPalette[6],cbPalette[5],cbPalette[7],cbPalette[8])) +
	scale_shape_manual(values=c(21,22,23,24)) +
	facet_grid(Body ~ .)
plt

# Check to see if the angular momentums of the torso and tail cancel eachother out.
sum(subset(ang_mom_data,Body == "torso" | Body == "tail")$norm_ang_mom)

# Check to see if the angular momentums of the torso, tail, and rear legs cancel eachother out.
sum(subset(ang_mom_data,Body == "torso" | Body == "tail" | Body == "both_rear_legs")$norm_ang_mom)

save_plot(base_path,"ang_mom_over_time",plt)

# Plot the ang_mom data within the time interval.
plt <- ggplot() +
	labs(title="Angular Momentum Over Time",x="Time",y="Angular Momentum") +
	theme(legend.position="bottom") +
	ylim(min=-0.15,max=0.15) +
	xlim(min=low_bound,max=upp_bound) +
	geom_rect(data=full_cps,aes(xmin=time_low_bound,ymin=-0.15,xmax=time_upp_bound,ymax=0.15),color="black",group=NA,alpha=0.4)  +
	geom_point(data=ang_mom_data, aes(x=Time,y=norm_ang_mom,group=Body,shape=Body,fill=Body),color="black",size=3) +
	scale_fill_manual(values=c(cbPalette[6],cbPalette[5],cbPalette[7],cbPalette[8])) +
	scale_shape_manual(values=c(21,22,23,24))
plt

save_plot(base_path,"ang_mom_over_limited_time",plt)

# Assess the angular momentums of the three main components we're interested in together.
sum(subset(ang_mom_data, Body == "torso" | Body == "tail")$Ang_Mom)
sum(subset(ang_mom_data, Body != "left_leg" & Body != "right_leg")$Ang_Mom)
sum(subset(ang_mom_data, Body == "torso" | Body == "tail" | Body == "both_rear_legs")$Ang_Mom)

# Get a subset of the ang_mom_data to remove times when we are in contact with the ground.
summary(ang_mom_data$Time)
ground_contact_ang_mom_data <- subset(ang_mom_data, Time %in% touch_data$Time)
flight_ang_mom_data <- subset(ang_mom_data, !(Time %in% touch_data$Time))
summary(ground_contact_ang_mom_data)
summary(flight_ang_mom_data)

sum(subset(ground_contact_ang_mom_data, Body == "torso" | Body == "tail" | Body == "both_rear_legs")$Ang_Mom)
sum(subset(flight_ang_mom_data, Body == "torso" | Body == "tail" | Body == "both_rear_legs")$Ang_Mom)

summary(ang_mom_data$Body)


time <- unified_data$Time
summary(time)
subset(time, time %% 0.2 == 0.0)