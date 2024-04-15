(module
  ;; Import necessary external values
  (import "env" "sensorValue" (global $sensorValue (mut f64)))
  (import "env" "setPoint" (global $setPoint f64))
  (import "env" "Kp" (global $Kp f64))
  (import "env" "Ki" (global $Ki f64))

  ;; Define globals for PI state
  (global $integralError (mut f64) (f64.const 0.0))
  (global $prevError (mut f64) (f64.const 0.0))

  ;; Function to calculate PI
  (func $calculatePID (export "calculateOutput") (result f64)
    (local $error f64)
    (local $output f64)

    ;; Calculate the current error
    (local.set $error
      (f64.sub
        (global.get $setPoint)
        (global.get $sensorValue)
      )
    )

    ;; Calculate integral of error
    (global.set $integralError
      (f64.add
        (global.get $integralError)
        (local.get $error)
      )
    )

    ;; Calculate PI output
    (local.set $output
      (f64.add
        (f64.mul (global.get $Kp) (local.get $error))
        (f64.mul (global.get $Ki) (global.get $integralError))
      )
    )

    ;; Return the output
    (local.get $output)
  )

  ;; Define memory and initial value for integral and previous error (if needed)
  (memory 1)
)
