API Reference
=============

This reference is generated from the stable package exports used for model
generation.

Configuration
-------------

.. autoclass:: pinocchio_models.BodyModelSpec
   :members:

.. autoclass:: pinocchio_models.BarbellSpec
   :members:

.. autoclass:: pinocchio_models.ExerciseConfig
   :members:

Builder Base
------------

.. autoclass:: pinocchio_models.ExerciseModelBuilder
   :members:

Exercise Builders
-----------------

.. autoclass:: pinocchio_models.SquatModelBuilder
   :members:

.. autoclass:: pinocchio_models.BenchPressModelBuilder
   :members:

.. autoclass:: pinocchio_models.DeadliftModelBuilder
   :members:

.. autoclass:: pinocchio_models.SnatchModelBuilder
   :members:

.. autoclass:: pinocchio_models.CleanAndJerkModelBuilder
   :members:

.. autoclass:: pinocchio_models.GaitModelBuilder
   :members:

.. autoclass:: pinocchio_models.SitToStandModelBuilder
   :members:

Convenience Functions
---------------------

.. autofunction:: pinocchio_models.build_squat_model

.. autofunction:: pinocchio_models.build_bench_press_model

.. autofunction:: pinocchio_models.build_deadlift_model

.. autofunction:: pinocchio_models.build_snatch_model

.. autofunction:: pinocchio_models.build_clean_and_jerk_model

.. autofunction:: pinocchio_models.build_gait_model

.. autofunction:: pinocchio_models.build_sit_to_stand_model

Exceptions
----------

.. autoclass:: pinocchio_models.PinocchioModelsError
   :members:

.. autoclass:: pinocchio_models.GeometryError
   :members:

.. autoclass:: pinocchio_models.URDFError
   :members:
