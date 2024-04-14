(module
  ;; Import external values and parameters
  (import "env" "space_temp" (global $space_temp (mut f64)))

  ;; PID parameters and states for heating and cooling
  (global $Kp_heating f64 (f64.const 5.0))
  (global $Ki_heating f64 (f64.const 1.0))
  (global $Kd_heating f64 (f64.const 0.0))
  (global $integral_heating (mut f64) (f64.const 0.0))
  (global $prev_error_heating (mut f64) (f64.const 0.0))
  
  (global $Kp_cooling f64 (f64.const 5.0))
  (global $Ki_cooling f64 (f64.const 1.0))
  (global $Kd_cooling f64 (f64.const 0.0))
  (global $integral_cooling (mut f64) (f64.const 0.0))
  (global $prev_error_cooling (mut f64) (f64.const 0.0))

  ;; Additional setpoints and operational parameters
  (global $setpoint f64 (f64.const 72.0))
  (global $deadband f64 (f64.const 5.0))
  (global $ahu_sat f64 (f64.const 55.0))
  (global $max_dat f64 (f64.const 90.0))
  (global $min_flow_heat f64 (f64.const 100.0))
  (global $max_flow_heat f64 (f64.const 850.0))
  (global $min_flow_cool f64 (f64.const 100.0))
  (global $max_flow_cool f64 (f64.const 1000.0))
  (global $satisfied_airflow f64 (f64.const 50.0))
  
  ;; Define memory for complex data management (if needed)
  (memory 1)

  ;; Function to calculate control logic and outputs
  (func $control_logic (result i32)
    (local $error f64)
    (local $output f64)
    (local $mode i32) ;; 0 for satisfied, 1 for heating, 2 for cooling

    ;; Calculate error
    (local.set $error
      (f64.sub
        (global.get $setpoint)
        (global.get $space_temp)
      )
    )

    ;; Check if heating or cooling is needed
    (if 
      (f64.gt (f64.abs (local.get $error)) (f64.div (global.get $deadband) (f64.const 2.0)))
      (then
        (if 
          (f64.gt (local.get $error) (f64.const 0.0))
          (then
            ;; Heating logic
            (local.set $output (call $calc_heating_pid (local.get $error) (f64.const 1.0)))
            (local.set $mode (i32.const 1))
          )
          (else
            ;; Cooling logic
            (local.set $output (call $calc_cooling_pid (f64.neg (local.get $error)) (f64.const 1.0)))
            (local.set $mode (i32.const 2))
          )
        )
      )
      (else
        ;; Satisfied logic
        (local.set $mode (i32.const 0))
      )
    )
    
    ;; Return mode as an example; more complex logic may involve returning multiple values
    (local.get $mode)
  )

  ;; Function to calculate heating PID
  (func $calc_heating_pid (param $error f64) (param $dt f64) (result f64)
    (local $derivative f64)
    (local $output f64)

    ;; Update the integral for heating
    (global.set $integral_heating
      (f64.add
        (global.get $integral_heating)
        (f64.mul
          (local.get $error)
          (local.get $dt)
        )
      )
    )

    ;; Calculate the derivative term
    (local.set $derivative
      (f64.div
        (f64.sub
          (local.get $error)
          (global.get $prev_error_heating)
        )
        (local.get $dt)
      )
    )

    ;; Calculate the output based on PID formula
    (local.set $output
      (f64.add
        (f64.mul
          (global.get $Kp_heating)
          (local.get $error)
        )
        (f64.add
          (f64.mul
            (global.get $Ki_heating)
            (global.get $integral_heating)
          )
          (f64.mul
            (global.get $Kd_heating)
            (local.get $derivative)
          )
        )
      )
    )

    ;; Update the previous error
    (global.set $prev_error_heating
      (local.get $error)
    )

    ;; Return the output
    (local.get $output)
  )


  ;; Function to calculate cooling PID
  (func $calc_cooling_pid (param $error f64) (param $dt f64) (result f64)
    (local $derivative f64)
    (local $output f64)

    ;; Update the integral for cooling
    (global.set $integral_cooling
      (f64.add
        (global.get $integral_cooling)
        (f64.mul
          (local.get $error)
          (local.get $dt)
        )
      )
    )

    ;; Calculate the derivative term
    (local.set $derivative
      (f64.div
        (f64.sub
          (local.get $error)
          (global.get $prev_error_cooling)
        )
        (local.get $dt)
      )
    )

    ;; Calculate the output based on PID formula
    (local.set $output
      (f64.add
        (f64.mul
          (global.get $Kp_cooling)
          (local.get $error)
        )
        (f64.add
          (f64.mul
            (global.get $Ki_cooling)
            (global.get $integral_cooling)
          )
          (f64.mul
            (global.get $Kd_cooling)
            (local.get $derivative)
          )
        )
      )
    )

    ;; Update the previous error
    (global.set $prev_error_cooling
      (local.get $error)
    )

    ;; Return the output
    (local.get $output)
  )


  ;; Export functions for external access
  (export "control_logic" (func $control_logic))
)
