from io import BytesIO

from backend.app import database
from backend.app.models import ChatChannel, ChatMessage, User


def test_seeded_channels_and_messages_are_listed(client) -> None:
    channels_response = client.get("/api/v1/channels")
    assert channels_response.status_code == 200
    channels = channels_response.json()
    channel_names = {channel["name"] for channel in channels}
    assert "general" in channel_names
    assert "anc2-purification" in channel_names

    anc2_channel = next(channel for channel in channels if channel["name"] == "anc2-purification")
    messages_response = client.get(f"/api/v1/channels/{anc2_channel['id']}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) >= 2
    assert any(message["referenced_workflow_title"] == "ANC2 Batch 1" for message in messages)


def test_channel_crudl_and_message_crudl(client) -> None:
    create_channel = client.post(
        "/api/v1/channels",
        json={
            "name": "sec-analysis",
            "topic": "Discuss SEC traces and pooled fraction choices.",
        },
    )
    assert create_channel.status_code == 201
    channel = create_channel.json()
    assert channel["name"] == "sec-analysis"

    update_channel = client.patch(
        f"/api/v1/channels/{channel['id']}",
        json={"topic": "Discuss SEC traces, SDS-PAGE, and pooling decisions."},
    )
    assert update_channel.status_code == 200
    assert "pooling decisions" in update_channel.json()["topic"]

    create_message = client.post(
        f"/api/v1/channels/{channel['id']}/messages",
        json={
            "body": "Uploading the first SEC comparison notes here.",
            "referenced_workflow_id": "workflow-anc2-batch-1",
        },
    )
    assert create_message.status_code == 201
    message = create_message.json()
    assert message["author_display_name"] == "Chen, Y."
    assert message["referenced_workflow_title"] == "ANC2 Batch 1"

    list_messages = client.get(f"/api/v1/channels/{channel['id']}/messages")
    assert list_messages.status_code == 200
    assert any(item["id"] == message["id"] for item in list_messages.json())

    update_message = client.patch(
        f"/api/v1/channels/{channel['id']}/messages/{message['id']}",
        json={
            "body": "Updated SEC comparison with preparative run notes.",
            "referenced_workflow_id": "workflow-anc2-batch-2",
            "referenced_experiment_id": None,
        },
    )
    assert update_message.status_code == 200
    assert update_message.json()["referenced_workflow_title"] == "ANC2 Batch 2"

    delete_message = client.delete(f"/api/v1/channels/{channel['id']}/messages/{message['id']}")
    assert delete_message.status_code == 204

    delete_channel = client.delete(f"/api/v1/channels/{channel['id']}")
    assert delete_channel.status_code == 204


def test_message_attachment_upload_and_listing(client) -> None:
    create_channel = client.post(
        "/api/v1/channels",
        json={"name": "gel-review", "topic": "Attach gel images for review."},
    )
    assert create_channel.status_code == 201
    channel_id = create_channel.json()["id"]

    create_message = client.post(
        f"/api/v1/channels/{channel_id}/messages",
        json={"body": "Here is the first gel image."},
    )
    assert create_message.status_code == 201
    message_id = create_message.json()["id"]

    upload_response = client.post(
        f"/api/v1/channels/{channel_id}/messages/{message_id}/attachments",
        files={"file": ("gel.png", BytesIO(b"fake-png-bytes"), "image/png")},
    )
    assert upload_response.status_code == 201
    attachment = upload_response.json()
    assert attachment["filename"] == "gel.png"

    attachments_response = client.get(f"/api/v1/channels/{channel_id}/messages/{message_id}/attachments")
    assert attachments_response.status_code == 200
    attachments = attachments_response.json()
    assert len(attachments) == 1
    assert attachments[0]["id"] == attachment["id"]


def test_chat_lab_scoping_and_permissions(client) -> None:
    with database.SessionLocal() as db:
      foreign_channel = ChatChannel(
          id="channel-foreign-lab",
          lab_id="other-lab",
          name="foreign-lab",
          topic="Should not be visible to the local lab user.",
          created_by_id="user-pi-ferretti",
      )
      db.add(foreign_channel)

      outsider = User(
          id="user-outsider",
          email="outsider@nmr-lab.local",
          display_name="Outsider, N.",
          role="student",
          lab_id="local-lab",
      )
      db.merge(outsider)
      protected_message = ChatMessage(
          id="message-protected",
          channel_id="channel-general",
          lab_id="local-lab",
          author_id="user-outsider",
          body="Only the author or a professor should be able to edit this.",
      )
      db.add(protected_message)
      db.commit()

    list_channels = client.get("/api/v1/channels")
    assert list_channels.status_code == 200
    assert all(channel["id"] != "channel-foreign-lab" for channel in list_channels.json())

    read_foreign_channel = client.get("/api/v1/channels/channel-foreign-lab")
    assert read_foreign_channel.status_code == 404

    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        user.role = "student"
        db.commit()

    forbidden_edit = client.patch(
        "/api/v1/channels/channel-general/messages/message-protected",
        json={
            "body": "Trying to edit another user's message as a student.",
            "referenced_workflow_id": None,
            "referenced_experiment_id": None,
        },
    )
    assert forbidden_edit.status_code == 403

    forbidden_delete = client.delete("/api/v1/channels/channel-general/messages/message-protected")
    assert forbidden_delete.status_code == 403

    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        user.role = "professor"
        db.commit()

    allowed_edit = client.patch(
        "/api/v1/channels/channel-general/messages/message-protected",
        json={
            "body": "Professor override applied.",
            "referenced_workflow_id": None,
            "referenced_experiment_id": None,
        },
    )
    assert allowed_edit.status_code == 200
    assert allowed_edit.json()["body"] == "Professor override applied."

    allowed_delete = client.delete("/api/v1/channels/channel-general/messages/message-protected")
    assert allowed_delete.status_code == 204
