from typing import Annotated, Any

from pydantic import BaseModel, Field

from prolific_mcp.client import get_client
from prolific_mcp.errors import ProlificAPIError
from prolific_mcp.server import mcp


async def _secret_exists(workspace_id: str) -> bool:
    response = await get_client().get("/hooks/secrets/", params={"workspace_id": workspace_id})
    results = response.get("results", []) if isinstance(response, dict) else []
    return bool(results)


class WebhookSecretStatus(BaseModel):
    workspace_id: str = Field(description="Workspace this status is for.")
    exists: bool = Field(
        description=(
            "Whether a webhook signing secret already exists for this workspace. "
            "True means proceed straight to create_webhook_subscription — no value "
            "is needed for that call. False means call create_webhook_secret first."
        )
    )


@mcp.tool(meta={"stability": "experimental"})
async def ensure_webhook_secret(
    workspace_id: Annotated[str, Field(description="Workspace to check.")],
) -> WebhookSecretStatus:
    """Check whether a webhook signing secret already exists for a workspace.

    Never returns the secret's value, even though the underlying API does —
    subscription creation only needs one to exist, not its value. If one
    already exists and you need to see it again (e.g. to reconfigure a
    receiver whose config you lost), that's `prolific hook secrets -w
    <workspace_id>` via the CLI, not an MCP tool — the value is deliberately
    never surfaced here or by any other tool in this server.
    """
    return WebhookSecretStatus(workspace_id=workspace_id, exists=await _secret_exists(workspace_id))


class WebhookSecret(BaseModel):
    workspace_id: str = Field(description="Workspace this secret belongs to.")
    value: str = Field(
        description=(
            "The signing secret. Hand this to whoever configures the receiving "
            "webhook endpoint to verify payload signatures — prolific-mcp itself "
            "never uses it. This is the only time it's returned; there is no "
            "tool to retrieve it again afterwards."
        )
    )


@mcp.tool(meta={"stability": "experimental"})
async def create_webhook_secret(
    workspace_id: Annotated[str, Field(description="Workspace to create a secret for.")],
    confirm_rotation: Annotated[
        bool,
        Field(
            description=(
                "Must be True to proceed if a secret already exists for this "
                "workspace. Creating a new secret immediately invalidates the "
                "old one, breaking any receiver still relying on it — this is "
                "a deliberate reset (suspected compromise, intentional rotation), "
                "not a way to recover a lost value."
            )
        ),
    ] = False,
) -> WebhookSecret:
    """Create the webhook signing secret required before any subscription can be created.

    Only needed once per workspace — call `ensure_webhook_secret` first and
    only call this when it reports `exists: false`. The value is returned
    exactly once; there is no tool to fetch it again afterwards.
    """
    if not confirm_rotation and await _secret_exists(workspace_id):
        raise ValueError(
            "A webhook secret already exists for this workspace. Creating a new one "
            "will immediately invalidate it, breaking any receiver relying on the "
            "existing value. Pass confirm_rotation=True to proceed anyway, or leave "
            "the existing secret in place — subscription creation only needs one to "
            "exist, not its value."
        )
    response = await get_client().post("/hooks/secrets/", json={"workspace_id": workspace_id})
    return WebhookSecret(workspace_id=workspace_id, value=response["value"])


@mcp.tool(meta={"stability": "experimental"})
async def list_webhook_event_types() -> Any:
    """List event types available to subscribe to, e.g. `study.status.change`.

    Pair with `create_webhook_subscription`.
    """
    return await get_client().get("/hooks/event-types/")


@mcp.tool(meta={"stability": "experimental"})
async def create_webhook_subscription(
    workspace_id: Annotated[str, Field(description="Workspace to create the subscription in.")],
    event_type: Annotated[
        str,
        Field(
            description=(
                "Event type to subscribe to, e.g. `study.status.change`. "
                "See `list_webhook_event_types` for the full list."
            )
        ),
    ],
    target_url: Annotated[
        str,
        Field(
            description=(
                "HTTPS URL Prolific will POST events to. Must be publicly "
                "reachable — not `localhost`."
            )
        ),
    ],
) -> Any:
    """Subscribe to a webhook event type and confirm it, in one step.

    Requires a webhook secret to already exist for the workspace — call
    `ensure_webhook_secret` first, and `create_webhook_secret` if it reports
    `exists: false`. Without one, the API rejects this with "Subscriptions
    can only be created for workspaces with a secret."

    Combines the API's create-then-confirm handshake into one call: the
    one-time confirmation secret returned in the response's `X-Hook-Secret`
    header is consumed immediately here and never returned to the caller.
    The subscription comes back already enabled (`is_enabled: true`).
    """
    client = get_client()
    subscription, headers = await client.post_with_headers(
        "/hooks/subscriptions/",
        json={"workspace_id": workspace_id, "event_type": event_type, "target_url": target_url},
    )
    subscription_id = subscription["id"]
    confirm_secret = headers["X-Hook-Secret"]

    try:
        return await client.post(
            f"/hooks/subscriptions/{subscription_id}/",
            json={"secret": confirm_secret},
        )
    except ProlificAPIError as exc:
        raise ProlificAPIError(
            exc.status_code,
            exc.body,
            message=(
                f"Subscription {subscription_id} was created but confirmation "
                f"failed: {exc}. It exists but is disabled (is_enabled: false) — "
                "delete it and retry, or investigate directly."
            ),
        ) from exc


@mcp.tool(meta={"stability": "experimental"})
async def list_webhook_subscriptions(
    workspace_id: Annotated[str, Field(description="Workspace to list subscriptions in.")],
    enabled: Annotated[
        bool,
        Field(
            description=(
                "Filter by enabled state. The API has no mode that returns both "
                "— call this twice (once with True, once with False) for the "
                "full picture."
            )
        ),
    ] = True,
    limit: Annotated[int, Field(ge=1, le=500, description="Page size.")] = 200,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
) -> Any:
    """List webhook subscriptions in a workspace.

    Pair with `update_webhook_subscription` or `delete_webhook_subscription`
    to act on a specific entry.
    """
    return await get_client().get(
        "/hooks/subscriptions",
        params={
            "workspace_id": workspace_id,
            "is_enabled": enabled,
            "limit": limit,
            "offset": offset,
        },
    )


@mcp.tool(meta={"stability": "experimental"})
async def update_webhook_subscription(
    subscription_id: Annotated[str, Field(description="ID of the subscription to update.")],
    event_type: Annotated[str | None, Field(description="New event type to subscribe to.")] = None,
    target_url: Annotated[str | None, Field(description="New target URL.")] = None,
    is_enabled: Annotated[
        bool | None,
        Field(
            description=(
                "Enable or disable the subscription. Prefer this over "
                "delete_webhook_subscription for a temporary pause."
            )
        ),
    ] = None,
) -> Any:
    """Update a webhook subscription. Only the fields you pass are changed.

    All fields are optional — omit anything you don't want to change.
    """
    payload = {
        key: value
        for key, value in {
            "event_type": event_type,
            "target_url": target_url,
            "is_enabled": is_enabled,
        }.items()
        if value is not None
    }
    return await get_client().patch(f"/hooks/subscriptions/{subscription_id}/", json=payload)


@mcp.tool(meta={"stability": "experimental"})
async def delete_webhook_subscription(
    subscription_id: Annotated[str, Field(description="ID of the subscription to delete.")],
) -> None:
    """Permanently delete a webhook subscription.

    To temporarily pause notifications instead, use `update_webhook_subscription`
    with `is_enabled=False`.
    """
    await get_client().delete(f"/hooks/subscriptions/{subscription_id}/")


@mcp.tool(meta={"stability": "experimental"})
async def list_webhook_events(
    subscription_id: Annotated[
        str, Field(description="Subscription to list delivered events for.")
    ],
    limit: Annotated[int, Field(ge=1, le=500, description="Page size.")] = 200,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
) -> Any:
    """List the audit log of events actually delivered for a subscription.

    Useful for reconciliation or debugging — confirming Prolific attempted
    delivery and what status it recorded, separate from whether your
    receiver's own processing succeeded.
    """
    return await get_client().get(
        f"/hooks/subscriptions/{subscription_id}/events/",
        params={"limit": limit, "offset": offset},
    )
