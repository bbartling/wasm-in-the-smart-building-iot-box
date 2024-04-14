(module
  ;; Import external values
  (import "env" "sensorValue" (global $sensorValue (mut f64)))
  (import "env" "setPoint" (global $setPoint f64))
  (import "env" "Kp" (global $Kp f64))
  (import "env" "Ki" (global $Ki f64))

  ;; Define the accumulated error internally
  (global $accumulatedError (mut f64) (f64.const 0.0))

  ;; Export the PID function
  (func $PI (export "calculateOutput") (result f64)
    (local $error f64)
    (local $integral f64)
    
    ;; Calculate error
    (local.set $error
      (f64.sub
        (global.get $setPoint)
        (global.get $sensorValue)
      )
    )
    
    ;; Calculate integral part
    (local.set $integral
      (f64.mul
        (global.get $Ki)
        (global.get $accumulatedError)
      )
    )

    ;; Calculate output: P + I and return the result
    (f64.add
      (f64.mul
        (global.get $Kp)
        (local.get $error)
      )
      (local.get $integral)
    )
  )

  ;; Memory definition (if needed for other purposes)
  (memory 1)
)
