-- Preparation-time (ETA) configuration per restaurant, with its OWN demand
-- thresholds (independent from delivery pricing). 1:1 with business_configuration.
CREATE TABLE "preparation_time_configuration" (
    "preparation_time_configuration_id" UUID NOT NULL,
    "business_config_id" UUID NOT NULL,
    "high_demand_threshold" INTEGER NOT NULL,
    "very_high_demand_threshold" INTEGER NOT NULL,
    "normal_prep_minutes" INTEGER NOT NULL,
    "high_demand_prep_minutes" INTEGER NOT NULL,
    "very_high_demand_prep_minutes" INTEGER NOT NULL,
    "buffer_minutes" INTEGER NOT NULL,
    CONSTRAINT "preparation_time_configuration_pkey" PRIMARY KEY ("preparation_time_configuration_id")
);

CREATE UNIQUE INDEX "preparation_time_configuration_business_config_id_key"
    ON "preparation_time_configuration"("business_config_id");

ALTER TABLE "preparation_time_configuration"
    ADD CONSTRAINT "preparation_time_configuration_business_config_id_fkey"
    FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id")
    ON DELETE CASCADE ON UPDATE CASCADE;

-- Order: delivery travel time snapshot (route duration), so the ETA can be
-- recomputed at confirmation without repeating routing.
ALTER TABLE "order" ADD COLUMN "route_duration_minutes" INTEGER;
