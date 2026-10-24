import * as Effect from "effect/Effect";

import { updateAgentAwarenessRegistrationPreferences } from "./remoteRegistration";

// The switch changes only this device's registration. Hosts link themselves to
// T3 Connect; their link-proof endpoint rejects requests from other machines.
export const setLiveActivityUpdatesEnabled = Effect.fn("setLiveActivityUpdatesEnabled")(
  function* (input: { readonly enabled: boolean; readonly previousEnabled: boolean }) {
    // Android applies the preference to its native notifications before the
    // relay request, so a failed request must put the previous value back.
    yield* updateAgentAwarenessRegistrationPreferences({
      liveActivitiesEnabled: input.enabled,
    }).pipe(
      Effect.onError(() =>
        updateAgentAwarenessRegistrationPreferences({
          liveActivitiesEnabled: input.previousEnabled,
        }).pipe(
          Effect.catchCause((cause) =>
            Effect.logWarning("Could not restore Live Activity device preference.", cause),
          ),
        ),
      ),
    );
  },
);
