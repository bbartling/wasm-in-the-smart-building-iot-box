
class VavBoxController:
    '''
    TODO add in -
    state machines for sensor reliability
    air flow PID control for damper
    integral windup prevention
    occupancy state for unoc setpoints
    '''
    def __init__(
        self,
        deadband=5,
        space_temp_setpoint=72,
        heat_min_flow=100,
        heat_max_flow=850,
        cool_min_flow=100,
        cool_max_flow=1000,
        satisfied_airflow_setpoint=50,
        ahu_sat=55,
        max_dat=90,
        vav_air_flow_volume=0,

        # heating PID params
        Kp_heating = 5,
        Ki_heating = 1.0,
        Kd_heating = 0,
        integral_heating = 0,
        prev_error_heating = 0,

        # cool PID params
        Kp_cooling = 5,
        Ki_cooling = 1.0,
        Kd_cooling = 0,
        integral_cooling = 0,
        prev_error_cooling=0,
    ):
        self.deadband = deadband
        self.heat_min_flow = heat_min_flow
        self.heat_max_flow = heat_max_flow
        self.cool_min_flow = cool_min_flow
        self.cool_max_flow = cool_max_flow
        self.satisfied_airflow_setpoint = satisfied_airflow_setpoint

        # AHU Supply Air Temperature
        self.ahu_sat = ahu_sat

        # Maximum Discharge Air Temperature
        self.max_dat = max_dat

        # Degrees Fahrenheit
        self.space_temp_setpoint = space_temp_setpoint

        # heating PID params
        self.Kp_heating = Kp_heating
        self.Ki_heating = Ki_heating
        self.Kd_heating = Kd_heating
        self.integral_heating = integral_heating
        self.prev_error_heating = prev_error_heating

        # cool PID params
        self.Kp_cooling = Kp_cooling
        self.Ki_cooling = Ki_cooling
        self.Kd_cooling = Kd_cooling
        self.integral_cooling = integral_cooling
        self.prev_error_cooling = prev_error_cooling


    def update_setpoint(self, space_temp_setpoint):
        self.space_temp_setpoint = space_temp_setpoint

    def calc_cooling_pid(self, error, dt=1):
        self.integral_cooling += error * dt
        derivative = (error - self.prev_error_cooling) / dt
        output = (self.Kp_cooling * error) + (self.Ki_cooling * self.integral_cooling) + (self.Kd_cooling * derivative)
        self.prev_error_cooling = error
        return output

    def calc_heating_pid(self, error, dt=1):
        self.integral_heating += error * dt
        derivative = (error - self.prev_error_heating) / dt
        output = (self.Kp_heating * error) + (self.Ki_heating * self.integral_heating) + (self.Kd_heating * derivative)
        self.prev_error_heating = error
        return output

    def control_logic(self, space_temp, dt=1):
        mode = "Satisfied"
        heating_demand = 0
        cooling_demand = 0

        # Calculate the error or deviation from setpoint
        error = self.space_temp_setpoint - space_temp

        # If error is within the deadband, system is satisfied; no action needed
        if abs(error) > self.deadband / 2:
            if error > 0:
                # Heating needed
                mode = "Heating"
                heating_demand = self.calc_heating_pid(error, dt)
            else:
                # Cooling needed
                mode = "Cooling"
                cooling_demand = self.calc_cooling_pid(-error, dt)

            # Limit the demands to a maximum of 100%
            heating_demand = max(min(heating_demand, 100), 0)
            cooling_demand = max(min(cooling_demand, 100), 0)
        else:
            # Satisfied: Use satisfied airflow setpoint
            airflow_setpoint = self.satisfied_airflow_setpoint
            dat_setpoint = self.ahu_sat
            return mode, dat_setpoint, airflow_setpoint, heating_demand, cooling_demand

        # Update DAT setpoint and airflow based on mode and the revised logic
        if mode == "Heating":
            if heating_demand <= 50:
                # Scale DAT setpoint linearly from ahu_sat to max_dat as heating demand goes from 0% to 50%
                dat_setpoint = self.ahu_sat + ((heating_demand / 50) * (self.max_dat - self.ahu_sat))
                airflow_setpoint = self.heat_min_flow
            else:
                # Keep DAT setpoint at max_dat and scale airflow setpoint from min to max as heating demand goes from 50% to 100%
                dat_setpoint = self.max_dat
                airflow_setpoint = self.heat_min_flow + (((heating_demand - 50) / 50) * (self.heat_max_flow - self.heat_min_flow))

        elif mode == "Cooling":
            dat_setpoint = self.ahu_sat
            airflow_setpoint = self.cool_min_flow + (cooling_demand * (self.cool_max_flow - self.cool_min_flow) / 100)

        # Ensure the airflow and DAT setpoints are within bounds
        airflow_setpoint = max(min(airflow_setpoint, self.heat_max_flow), self.heat_min_flow)
        dat_setpoint = max(min(dat_setpoint, self.max_dat), self.ahu_sat)

        return mode, dat_setpoint, airflow_setpoint, heating_demand, cooling_demand


def simulate():
    vav = VavBoxController()

    # Constant temperature to test cooling and PID integral effect.
    satisfied_temp = 73  # within dead band
    constant_cooling_temp = 76
    constant_heating_temp = 68
    steps = 30 

    print("\nTesting Heating Demand with Constant Temperature outside Deadband")
    for step in range(10):
        current_temp = constant_heating_temp
        mode, dat_setpoint, airflow_setpoint, heating_demand, cooling_demand = vav.control_logic(space_temp=current_temp)
        print(f"************* STEP: {step+1} *************")
        print(f"Zone Temp = {current_temp:.2f}F, Zone Setpoint = {vav.space_temp_setpoint}F")
        print(f"Mode = {mode}, DAT Setpoint = {dat_setpoint:.2f}F, Airflow Setpoint = {airflow_setpoint}")
        print(f"Heating PID = {heating_demand:.2f}%, error = {vav.prev_error_heating:.2f}, integral = {vav.integral_heating:.2f}")
        print(f"Cooling PID = {cooling_demand:.2f}%, error = {vav.prev_error_cooling:.2f}, integral = {vav.integral_cooling:.2f}")

    print("\nTesting Satisfied Mode within Deadband")
    for step in range(5):
        current_temp = satisfied_temp
        mode, dat_setpoint, airflow_setpoint, heating_demand, cooling_demand = vav.control_logic(space_temp=current_temp)
        print(f"************* STEP: {step+1} *************")
        print(f"Zone Temp = {current_temp:.2f}F, Zone Setpoint = {vav.space_temp_setpoint}F")
        print(f"Mode = {mode}, DAT Setpoint = {dat_setpoint:.2f}F, Airflow Setpoint = {airflow_setpoint}")
        print(f"Heating PID = {heating_demand:.2f}%, error = {vav.prev_error_heating:.2f}, integral = {vav.integral_heating:.2f}")
        print(f"Cooling PID = {cooling_demand:.2f}%, error = {vav.prev_error_cooling:.2f}, integral = {vav.integral_cooling:.2f}")

    print("\nTesting Cooling Demand with Constant Temperature outside Deadband")
    for step in range(5, steps):
        current_temp = constant_cooling_temp
        mode, dat_setpoint, airflow_setpoint, heating_demand, cooling_demand = vav.control_logic(space_temp=current_temp)
        print(f"************* STEP: {step+1} *************")
        print(f"Zone Temp = {current_temp:.2f}F, Zone Setpoint = {vav.space_temp_setpoint}F")
        print(f"Mode = {mode}, DAT Setpoint = {dat_setpoint:.2f}F, Airflow Setpoint = {airflow_setpoint}")
        print(f"Heating PID = {heating_demand:.2f}%, error = {vav.prev_error_heating:.2f}, integral = {vav.integral_heating:.2f}")
        print(f"Cooling PID = {cooling_demand:.2f}%, error = {vav.prev_error_cooling:.2f}, integral = {vav.integral_cooling:.2f}")

simulate()

