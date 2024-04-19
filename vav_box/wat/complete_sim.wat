(module
  ;; Import external values and parameters
  (import "env" "zone_air_temp" (global $zone_air_temp (mut f64)))
  (import "env" "ahu_supply_air_temp" (global $ahu_supply_air_temp (mut f64)))

  ;; PID parameters for heating and cooling (no derivative term)
  (global $Kp_heating f64 (f64.const 5.0))
  (global $Ki_heating f64 (f64.const 1.0))
  (global $integral_heating (mut f64) (f64.const 0.0))

  (global $Kp_cooling f64 (f64.const 5.0))
  (global $Ki_cooling f64 (f64.const 1.0))
  (global $integral_cooling (mut f64) (f64.const 0.0))

  ;; Outputs for heating and cooling
  (global $pid_output_heating (mut f64) (f64.const 0.0))
  (global $pid_output_cooling (mut f64) (f64.const 0.0))

  ;; Additional zone_air_temp_setpoints and operational parameters
  (global $zone_air_temp_setpoint f64 (f64.const 72.0))
  (global $zone_air_temp_deadband f64 (f64.const 5.0))

  ;; Define global variables for mode, zone_air_temp_error
  (global $mode (mut i32) (i32.const 0))
  (global $zone_air_temp_error (mut f64) (f64.const 0.0))

  ;; vars for vav box heating air reset
  (global $max_discharge_air_temp (mut f64) (f64.const 110))
  (global $discharge_air_temp_setpoint (mut f64) (f64.const 0))

  ;; vars for vav box air flow reset
  (global $discharge_air_flow_setpoint (mut f64) (f64.const 0))
  (global $clg_flow_min_air_flow_setpoint (mut f64) (f64.const 250))
  (global $clg_flow_max_air_flow_setpoint (mut f64) (f64.const 1000))
  (global $satisfied_flow_min_air_flow_setpoint (mut f64) (f64.const 150))
  (global $htg_flow_min_air_flow_setpoint (mut f64) (f64.const 200))
  (global $htg_flow_max_air_flow_setpoint (mut f64) (f64.const 750))

  ;; Generic PI calculation function that updates global state
  (func $calculate_pid
    (param $zone_air_temp_error f64) 
    (param $mode i32)
    (local $Kp f64)
    (local $Ki f64)
    (local $integral f64)
    (local $output f64)
    (local $initial_integral_heating f64)
    (local $initial_integral_cooling f64)
    (local $tolerance f64)

    ;; Store initial values of integrals
    (local.set $initial_integral_heating (global.get $integral_heating))
    (local.set $initial_integral_cooling (global.get $integral_cooling))

    ;; Corrected: Set the value of $tolerance after declaring
    (local.set $tolerance (f64.const 0.000001))

    (if (i32.eq (local.get $mode) (i32.const 1))
      (then
        (local.set $Kp (global.get $Kp_heating))
        (local.set $Ki (global.get $Ki_heating))
        (local.set $integral (global.get $integral_heating))
        (global.set $integral_heating
          (f64.add (local.get $integral) (local.get $zone_air_temp_error)))
        (local.set $output
          (f64.add
            (f64.mul (local.get $Kp) (local.get $zone_air_temp_error))
            (f64.mul (local.get $Ki) (local.get $integral))
          )
        )
        ;; Cap the pid output at 100
        (if (f64.gt (local.get $output) (f64.const 100.0))
          (then
            (local.set $output (f64.const 100.0))
            (global.set $integral_heating (local.get $initial_integral_heating))
          )
        )
        (global.set $pid_output_heating (local.get $output))
        (global.set $pid_output_cooling (f64.const 0.0))
        (global.set $integral_cooling (f64.const 0.0))
      )
      (else
        (if (i32.eq (local.get $mode) (i32.const 2)) ;; Cooling mode
          (then
            (local.set $Kp (global.get $Kp_cooling))
            (local.set $Ki (global.get $Ki_cooling))
            (local.set $integral (global.get $integral_cooling))
            (global.set $integral_cooling
              (f64.add (local.get $integral) (local.get $zone_air_temp_error)))
            (local.set $output
              (f64.abs    ;; ensure output is always positive
                (f64.add
                  (f64.mul (local.get $Kp) (local.get $zone_air_temp_error))
                  (f64.mul (local.get $Ki) (local.get $initial_integral_cooling))
                )
              )
            )
            ;; Cap the output at 100
            (if (f64.gt (local.get $output) (f64.const 100.0))
              (then
                (local.set $output (f64.const 100.0))
                (global.set $integral_cooling (local.get $initial_integral_cooling))
              )
            )
            (global.set $pid_output_cooling (local.get $output))
            (global.set $pid_output_heating (f64.const 0.0)) ;; Reset heating output
            (global.set $integral_heating (f64.const 0.0)) ;; Reset heating integral
          )
          (else ;; Satisfied mode
            (global.set $integral_heating (f64.const 0.0))
            (global.set $integral_cooling (f64.const 0.0))
            (global.set $pid_output_heating (f64.const 0.0))
            (global.set $pid_output_cooling (f64.const 0.0))
          )
        )
      )
    )
  )


  ;; Function to compute a reset calc between a min and max
  ;; used for heating data linear reset and air flow setpoint
  (func $interpolate_output (param $pid_out_calc f64) (param $max_ f64) (param $min_ f64) (result f64)
    (local $scaled_output f64)
    (local $range_difference f64)
    (local $interpolated_value f64)

    ;; Scale pid_out_calc to a 0-1 range
    (local.set $scaled_output
      (f64.div
        (local.get $pid_out_calc)
        (f64.const 100)
      )
    )

    ;; Calculate the difference between max_ and min_
    (local.set $range_difference
      (f64.sub
        (local.get $max_)
        (local.get $min_)
      )
    )

    ;; Calculate the interpolated value using the scaled output
    (local.set $interpolated_value
      (f64.add
        (local.get $min_)
        (f64.mul
          (local.get $range_difference)
          (local.get $scaled_output)
        )
      )
    )

    ;; Return the interpolated value
    (return (local.get $interpolated_value))
  )

  ;; Function to compute discharge_air_temp_setpoint
  (func $calculate_discharge_air_flow_setpoint
    (param $mode i32)  ;; Mode parameter

    ;; Check if mode is 1 (Heating)
    (if (i32.eq (local.get $mode) (i32.const 1))
      (then
        ;; Heating mode: Perform linear reset calculation
        ;;  if heating pid is greater than 50%
        (if (f64.ge (global.get $pid_output_heating) (f64.const 50.0))
          (then
            ;; Call the interpolate_output function 
            ;;  set the result to global $discharge_air_flow_setpoint
            (global.set $discharge_air_flow_setpoint
              (call $interpolate_output
                (global.get $pid_output_heating)
                (global.get $htg_flow_max_air_flow_setpoint)
                (global.get $htg_flow_min_air_flow_setpoint)
              )
            )
          )
          (else
            ;; When pid_output_heating is below 50%
            ;; set to htg_flow_min_air_flow_setpoint
            (global.set $discharge_air_flow_setpoint
              (global.get $htg_flow_min_air_flow_setpoint)
            )
          )
        )
      )
      (else
        ;; Check if mode is 2 (Cooling)
        (if (i32.eq (local.get $mode) (i32.const 2))
          (then
            ;; Cooling mode: Perform linear reset calculation
            (global.set $discharge_air_flow_setpoint
              (call $interpolate_output
                (global.get $pid_output_cooling)
                (global.get $clg_flow_max_air_flow_setpoint)
                (global.get $clg_flow_min_air_flow_setpoint)
              )
            )
          )
          (else
            ;; Satisfied mode: Set discharge_air_flow_setpoint 
            ;; to satisfied_flow_min_air_flow_setpoint
            (global.set $discharge_air_flow_setpoint
              (global.get $satisfied_flow_min_air_flow_setpoint)
            )
          )
        )
      )
    )
  )


  ;; Function to compute discharge_air_temp_setpoint
  (func $calculate_discharge_air_temp_setpoint
    (param $mode i32)  ;; Mode parameter

    ;; Check if mode is 1 (Heating)
    (if (i32.eq (local.get $mode) (i32.const 1))
      (then
        ;; Heating mode: Perform linear reset calculation
        ;; for discharge_air_temp_setpoint
        (if (f64.le (global.get $pid_output_heating) (f64.const 50.0))
          (then
            ;; Call the interpolate_output function 
            ;; set the result to global $discharge_air_temp_setpoint
            (global.set $discharge_air_temp_setpoint
              (call $interpolate_output

                ;; pass params into the $interpolate_output func
                (global.get $pid_output_heating)  
                (global.get $max_discharge_air_temp)         
                (global.get $ahu_supply_air_temp)
              )
            )
          )
          (else
            ;; When pid_output_heating is above 50
            ;; set discharge_air_temp_setpoint to max_discharge_air_temp
            global.get $max_discharge_air_temp
            global.set $discharge_air_temp_setpoint
          )
        )
      )
      (else
        ;; For cooling mode or other modes
        ;; set discharge_air_temp_setpoint to ahu_supply_air_temp
        global.get $ahu_supply_air_temp
        global.set $discharge_air_temp_setpoint
      )
    )
  )

  ;; Control logic function that updates global state
  (func $control_logic
    (local $zone_air_temp_error f64)
    ;; Calculate zone_air_temp_error
    (local.set $zone_air_temp_error
      (f64.sub (global.get $zone_air_temp_setpoint) (global.get $zone_air_temp)))
    (global.set $zone_air_temp_error (local.get $zone_air_temp_error))

    ;; Determine the mode based on the zone_air_temp_error
    (if (f64.gt (f64.abs (local.get $zone_air_temp_error)) (f64.div (global.get $zone_air_temp_deadband) (f64.const 2.0)))
      (then
        (if (f64.gt (local.get $zone_air_temp_error) (f64.const 0.0))
          (then 
            (global.set $mode (i32.const 1))  ;; Heating
          )
          (else
            (global.set $mode (i32.const 2))  ;; Cooling
          )
        )
      )
      (else
        (global.set $mode (i32.const 0))  ;; Satisfied
      )
    )
    ;; Update output using the PID calculation
    (call $calculate_pid (local.get $zone_air_temp_error) (global.get $mode))
    (call $calculate_discharge_air_temp_setpoint (global.get $mode))
    (call $calculate_discharge_air_flow_setpoint (global.get $mode))
  )

  ;; Export functions and globals for external access
  (export "pid_output_heating" (global $pid_output_heating))
  (export "pid_output_cooling" (global $pid_output_cooling))
  (export "mode" (global $mode))
  (export "integral_heating" (global $integral_heating))
  (export "integral_cooling" (global $integral_cooling))
  (export "control_mode" (global $mode))
  (export "zone_air_temp_error" (global $zone_air_temp_error))
  (export "discharge_air_temp_setpoint" (global $discharge_air_temp_setpoint))
  (export "discharge_air_flow_setpoint" (global $discharge_air_flow_setpoint)) 
  (export "control_logic" (func $control_logic))
)
