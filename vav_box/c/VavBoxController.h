// VavBoxController.h

#ifndef VAVBOXCONTROLLER_H
#define VAVBOXCONTROLLER_H

#include <stddef.h>

typedef struct
{
    double deadband;
    double space_temp_setpoint;
    double heat_min_flow;
    double heat_max_flow;
    double cool_min_flow;
    double cool_max_flow;
    double satisfied_airflow_setpoint;
    double ahu_sat;
    double max_dat;

    // PID parameters and state for heating
    double Kp_heating, Ki_heating, Kd_heating, integral_heating, prev_error_heating;

    // PID parameters and state for cooling
    double Kp_cooling, Ki_cooling, Kd_cooling, integral_cooling, prev_error_cooling;
} VavBoxController;

// Adjusted function declaration in VavBoxController.h

void VavBoxController_init(
    VavBoxController *self, 
    double deadband, 
    double space_temp_setpoint, 
    double heat_min_flow, 
    double heat_max_flow, 
    double cool_min_flow, 
    double cool_max_flow, 
    double satisfied_airflow_setpoint, 
    double ahu_sat, 
    double max_dat,
    double Kp_heating, double Ki_heating, double Kd_heating,
    double Kp_cooling, double Ki_cooling, double Kd_cooling
);


double calc_heating_pid(VavBoxController *self, double error, double dt);
double calc_cooling_pid(VavBoxController *self, double error, double dt);
void update_setpoint(VavBoxController *self, double space_temp_setpoint);

void control_logic(
    VavBoxController *self,
    double space_temp,
    double dt,
    double *mode,
    double *dat_setpoint,
    double *airflow_setpoint,
    double *heating_demand,
    double *cooling_demand);

#endif // VAVBOXCONTROLLER_H
