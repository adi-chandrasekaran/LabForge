PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc```\xf8"
    b"\x0f\x00\x01\x04\x01\x00_\xc2\x02\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_workflow_step_attachment_upload_list_and_content(client) -> None:
    upload_response = client.post(
        "/api/v1/workflows/workflow-anc2-batch-1/steps/b1-08/attachments",
        files={"file": ("gel-image.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201
    attachment = upload_response.json()
    assert attachment["owner_type"] == "workflow_step"
    assert attachment["owner_id"] == "b1-08"
    assert attachment["filename"] == "gel-image.png"
    assert attachment["download_url"].endswith(f"/api/v1/attachments/{attachment['id']}/content")

    list_response = client.get("/api/v1/workflows/workflow-anc2-batch-1/steps/b1-08/attachments")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == attachment["id"]

    workflow_response = client.get("/api/v1/workflows/workflow-anc2-batch-1")
    assert workflow_response.status_code == 200
    sds_page_step = next(step for step in workflow_response.json()["steps"] if step["id"] == "b1-08")
    assert sds_page_step["attachments"][0]["filename"] == "gel-image.png"

    content_response = client.get(f"/api/v1/attachments/{attachment['id']}/content")
    assert content_response.status_code == 200
    assert content_response.headers["content-type"] == "image/png"

    delete_response = client.delete(f"/api/v1/attachments/{attachment['id']}")
    assert delete_response.status_code == 204

    list_after_delete = client.get("/api/v1/workflows/workflow-anc2-batch-1/steps/b1-08/attachments")
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []

    deleted_content_response = client.get(f"/api/v1/attachments/{attachment['id']}/content")
    assert deleted_content_response.status_code == 404


def test_experiment_step_run_attachment_upload_and_invalid_content_type(client) -> None:
    instantiate_response = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "ANC2 Attachment Run",
            "experiment_date": "2026-07-15",
            "workflow_ids": ["workflow-anc2-batch-1", "workflow-anc2-batch-2"],
            "notes": "",
        },
    )
    assert instantiate_response.status_code == 201
    experiment = instantiate_response.json()
    batch_1_run = next(
        workflow_run for workflow_run in experiment["workflow_runs"] if workflow_run["source_workflow_id"] == "workflow-anc2-batch-1"
    )
    dialysis_step_run = next(step_run for step_run in batch_1_run["step_runs"] if step_run["label"] == "Dialysis")

    invalid_response = client.post(
        f"/api/v1/experiments/{experiment['id']}/workflow-runs/{batch_1_run['id']}/steps/{dialysis_step_run['id']}/attachments",
        files={"file": ("not-image.txt", b"plain text", "text/plain")},
    )
    assert invalid_response.status_code == 400

    upload_response = client.post(
        f"/api/v1/experiments/{experiment['id']}/workflow-runs/{batch_1_run['id']}/steps/{dialysis_step_run['id']}/attachments",
        files={"file": ("dialysis-note.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201
    attachment = upload_response.json()
    assert attachment["owner_type"] == "experiment_step_run"
    assert attachment["owner_id"] == dialysis_step_run["id"]

    list_response = client.get(
        f"/api/v1/experiments/{experiment['id']}/workflow-runs/{batch_1_run['id']}/steps/{dialysis_step_run['id']}/attachments"
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["filename"] == "dialysis-note.png"

    experiment_response = client.get(f"/api/v1/experiments/{experiment['id']}")
    assert experiment_response.status_code == 200
    reloaded_batch_1_run = next(
        workflow_run for workflow_run in experiment_response.json()["workflow_runs"] if workflow_run["id"] == batch_1_run["id"]
    )
    reloaded_dialysis = next(step_run for step_run in reloaded_batch_1_run["step_runs"] if step_run["id"] == dialysis_step_run["id"])
    assert reloaded_dialysis["attachments"][0]["filename"] == "dialysis-note.png"

    delete_response = client.delete(f"/api/v1/attachments/{attachment['id']}")
    assert delete_response.status_code == 204

    second_delete_response = client.delete(f"/api/v1/attachments/{attachment['id']}")
    assert second_delete_response.status_code == 404
