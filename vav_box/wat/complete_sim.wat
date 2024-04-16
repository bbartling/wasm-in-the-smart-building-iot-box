(module
  ;; Import external values and parameters
  (import "env" "space_temp" (global $space_temp (mut f64)))

  ;; PID parameters for heating and cooling (no derivative term)
  (global $Kp_heating f64 (f64.const 1.0))
  (global $Ki_heating f64 (f64.const 0.15))
  (global $integral_heating (mut f64) (f64.const 0.0))

  (global $Kp_cooling f64 (f64.const 1.0))
  (global $Ki_cooling f64 (f64.const 0.15))
  (global $integral_cooling (mut f64) (f64.const 0.0))

  ;; Additional setpoints and operational parameters
  (global $setpoint f64 (f64.const 72.0))
  (global $deadband f64 (f64.const 5.0))

  ;; Define global variables for mode, error, and output
  (global $mode (mut i32) (i32.const 0))
  (global $error (mut f64) (f64.const 0.0))
  (global $output (mut f64) (f64.const 0.0))

  ;; Generic PI calculation function that updates global state
  (func $calculate_pid
    (param $error f64) 
    (param $mode i32)
    (local $Kp f64)
    (local $Ki f64)
    (local $integral f64)
    (local $output f64)

    (if (i32.eq (local.get $mode) (i32.const 1)) ;; Heating mode
      (then
        (local.set $Kp (global.get $Kp_heating))
        (local.set $Ki (global.get $Ki_heating))
        (local.set $integral (global.get $integral_heating))
        (global.set $integral_heating
          (f64.add (local.get $integral) (local.get $error)))
        ;; Else branch for cooling
      ) 
      (else
        (local.set $Kp (global.get $Kp_cooling))
        (local.set $Ki (global.get $Ki_cooling))
        (local.set $integral (global.get $integral_cooling))
        (global.set $integral_cooling
          (f64.add (local.get $integral) (local.get $error)))
      )
    )
    (local.set $output
      (f64.add
        (f64.mul (local.get $Kp) (local.get $error))
        (f64.mul (local.get $Ki) (local.get $integral))
      )
    )
    (global.set $output (local.get $output))
  )

  ;; Control logic function that updates global state
  (func $control_logic
    (local $error f64)
    ;; Calculate error
    (local.set $error
      (f64.sub (global.get $setpoint) (global.get $space_temp)))
    (global.set $error (local.get $error))

    ;; Determine the mode based on the error
    (if (f64.gt (f64.abs (local.get $error)) (f64.div (global.get $deadband) (f64.const 2.0)))
      (then
        (if (f64.gt (local.get $error) (f64.const 0.0))
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
    (call $calculate_pid (local.get $error) (global.get $mode))
  )

  ;; Export functions and globals for external access
  (export "output" (global $output))
  (export "mode" (global $mode))
  (export "integral_heating" (global $integral_heating))
  (export "integral_cooling" (global $integral_cooling))
  (export "control_mode" (global $mode))
  (export "error" (global $error))
  (export "control_logic" (func $control_logic))
)
