// VavBoxController.c

#include "VavBoxController.h"
#include <math.h>
#include <stdlib.h>

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

    // Heating PID params
    double Kp_heating, double Ki_heating, double Kd_heating,
    // Cooling PID params
    double Kp_cooling, double Ki_cooling, double Kd_cooling)
{
    self->deadband = deadband;
    self->space_temp_setpoint = space_temp_setpoint;
    self->heat_min_flow = heat_min_flow;
    self->heat_max_flow = heat_max_flow;
    self->cool_min_flow = cool_min_flow;
    self->cool_max_flow = cool_max_flow;
    self->satisfied_airflow_setpoint = satisfied_airflow_setpoint;
    self->ahu_sat = ahu_sat;
    self->max_dat = max_dat;

    // Initialize PID parameters for heating
    self->Kp_heating = Kp_heating;
    self->Ki_heating = Ki_heating;
    self->Kd_heating = Kd_heating;
    self->integral_heating = 0.0;   // Start with no integral action
    self->prev_error_heating = 0.0; // And no previous error

    // Initialize PID parameters for cooling
    self->Kp_cooling = Kp_cooling;
    self->Ki_cooling = Ki_cooling;
    self->Kd_cooling = Kd_cooling;
    self->integral_cooling = 0.0;   // Start integral val
    self->prev_error_cooling = 0.0; // Start previous val
}

double calc_heating_pid(VavBoxController *self, double error, double dt)
{
    self->integral_heating += error * dt;
    double derivative = (error - self->prev_error_heating) / dt;
    double output = self->Kp_heating * error +
                    self->Ki_heating * self->integral_heating +
                    self->Kd_heating * derivative;
    self->prev_error_heating = error;
    return output;
}

double calc_cooling_pid(VavBoxController *self, double error, double dt)
{
    self->integral_cooling += error * dt;
    double derivative = (error - self->prev_error_cooling) / dt;
    double output = self->Kp_cooling * error +
                    self->Ki_cooling * self->integral_cooling +
                    self->Kd_cooling * derivative;
    self->prev_error_cooling = error;
    return output;
}

void update_setpoint(VavBoxController *self, double space_temp_setpoint)
{
    self->space_temp_setpoint = space_temp_setpoint;
}

void control_logic(
    VavBoxController *self,
    double space_temp,
    double dt,
    double *mode,
    double *dat_setpoint,
    double *airflow_setpoint,
    double *heating_demand,
    double *cooling_demand)
{
    // Calculate the error or deviation from setpoint
    double error = self->space_temp_setpoint - space_temp;

    // Reset demands
    *heating_demand = 0;
    *cooling_demand = 0;

    // Determine mode based on error and deadband
    if (fabs(error) <= self->deadband / 2)
    {
        // System is within deadband, no heating or cooling needed
        *mode = 0;                     // Satisfied mode
        *dat_setpoint = self->ahu_sat; // Default to supply air temperature
        *airflow_setpoint = self->satisfied_airflow_setpoint;
    }
    else 
    {
        if (error > 0)
        {
            // Heating needed
            *mode = 1; // Heating mode
            *heating_demand = calc_heating_pid(self, error, dt);
            
            if (*heating_demand <= 50) {
                // Scale DAT setpoint from AHU SAT to MAX DAT as heating demand goes from 0% to 50%
                *dat_setpoint = self->ahu_sat + ((*heating_demand / 50) * (self->max_dat - self->ahu_sat));
                *airflow_setpoint = self->heat_min_flow;
            } else {
                // Keep DAT setpoint at MAX DAT and scale airflow setpoint from MIN to MAX flow as heating demand goes from 50% to 100%
                *dat_setpoint = self->max_dat;
                *airflow_setpoint = self->heat_min_flow + (((*heating_demand - 50) / 50) * (self->heat_max_flow - self->heat_min_flow));
            }
        }
        else
        {
            // Cooling needed
            *mode = 2; // Cooling mode
            *cooling_demand = calc_cooling_pid(self, -error, dt); // Use -error to make demand positive
            *dat_setpoint = self->ahu_sat; // Assume DAT setpoint does not change for cooling
            *airflow_setpoint = self->cool_min_flow + (*cooling_demand * (self->cool_max_flow - self->cool_min_flow) / 100);
        }

        // Ensure demands are within bounds [0, 100]
        *heating_demand = fmax(0, fmin(*heating_demand, 100));
        *cooling_demand = fmax(0, fmin(*cooling_demand, 100));
    }
}
