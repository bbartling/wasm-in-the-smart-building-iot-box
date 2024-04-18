(module
  ;; Import external values and parameters
  (import "env" "space_temp" (global $space_temp (mut f64)))

  ;; PID parameters for heating and cooling (no derivative term)
  (global $Kp_heating f64 (f64.const 5.0))
  (global $Ki_heating f64 (f64.const 1.0))
  (global $integral_heating (mut f64) (f64.const 0.0))

  (global $Kp_cooling f64 (f64.const 5.0))
  (global $Ki_cooling f64 (f64.const 1.0))
  (global $integral_cooling (mut f64) (f64.const 0.0))

  ;; Outputs for heating and cooling
  (global $output_heating (mut f64) (f64.const 0.0))
  (global $output_cooling (mut f64) (f64.const 0.0))

  ;; Additional setpoints and operational parameters
  (global $setpoint f64 (f64.const 72.0))
  (global $deadband f64 (f64.const 5.0))

  ;; Define global variables for mode, error
  (global $mode (mut i32) (i32.const 0))
  (global $error (mut f64) (f64.const 0.0))

  ;; Generic PI calculation function that updates global state
  (func $calculate_pid
    (param $error f64) 
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

    (if (i32.eq (local.get $mode) (i32.const 1)) ;; Heating mode
      (then
        (local.set $Kp (global.get $Kp_heating))
        (local.set $Ki (global.get $Ki_heating))
        (local.set $integral (global.get $integral_heating))
        (global.set $integral_heating
          (f64.add (local.get $integral) (local.get $error)))
        (local.set $output
          (f64.add
            (f64.mul (local.get $Kp) (local.get $error))
            (f64.mul (local.get $Ki) (local.get $integral))
          )
        )
        ;; Cap the output at 100
        (if (f64.gt (local.get $output) (f64.const 100.0))
          (then
            (local.set $output (f64.const 100.0))
            (global.set $integral_heating (local.get $initial_integral_heating))
          )
        )

        (global.set $output_heating (local.get $output))
        (global.set $output_cooling (f64.const 0.0)) ;; Reset cooling output
        (global.set $integral_cooling (f64.const 0.0)) ;; Reset cooling integral
      )
      (else
        (if (i32.eq (local.get $mode) (i32.const 2)) ;; Cooling mode
          (then
            (local.set $Kp (global.get $Kp_cooling))
            (local.set $Ki (global.get $Ki_cooling))
            (local.set $integral (global.get $integral_cooling))
            (global.set $integral_cooling
              (f64.add (local.get $integral) (local.get $error)))
            (local.set $output
              (f64.add
                (f64.mul (local.get $Kp) (local.get $error))
                (f64.mul (local.get $Ki) (local.get $initial_integral_cooling))
              )
            )
            ;; Cap the output at 100
            ;; minus values for cooling PI
            (if (f64.lt (local.get $output) (f64.const -100.0))
              (then
                (local.set $output (f64.const 100.0))
                (global.set $integral_cooling (local.get $initial_integral_cooling))
              )
            )

            (global.set $output_cooling (local.get $output))
            (global.set $output_heating (f64.const 0.0)) ;; Reset heating output
            (global.set $integral_heating (f64.const 0.0)) ;; Reset heating integral
          )
          (else ;; Satisfied mode
            (global.set $integral_heating (f64.const 0.0))
            (global.set $integral_cooling (f64.const 0.0))
            (global.set $output_heating (f64.const 0.0))
            (global.set $output_cooling (f64.const 0.0))
          )
        )
      )
    )
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
  (export "output_heating" (global $output_heating))
  (export "output_cooling" (global $output_cooling))
  (export "mode" (global $mode))
  (export "integral_heating" (global $integral_heating))
  (export "integral_cooling" (global $integral_cooling))
  (export "control_mode" (global $mode))
  (export "error" (global $error))
  (export "control_logic" (func $control_logic))
)
