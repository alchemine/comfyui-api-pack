import pytest

MOVED_NODES = [
    "LoadWorkflow",
    "ApiGenerate",
    "ApiSubmit",
    "ApiCollect",
    "GrokGenerate",
    "GrokSubmit",
    "GrokCollect",
    "OpenAIInference",
]


@pytest.mark.parametrize("node_id", MOVED_NODES)
def test_node_id_is_registered(mappings, node_id):
    assert node_id in mappings


@pytest.mark.parametrize("node_id", MOVED_NODES)
def test_node_is_in_api_pack_category(mappings, node_id):
    assert mappings[node_id].CATEGORY.startswith("ApiPack/")


def test_load_workflow_reads_inside_workflows(pack, comfy_dirs):
    api = pack("api")
    workflows = comfy_dirs.user / "default" / "workflows"
    (workflows / "sub").mkdir()
    (workflows / "sub" / "wf.json").write_text("{}")

    assert api.LoadWorkflow().load("sub/wf.json") == ("{}",)


def test_load_workflow_filename_cannot_leave_workflows(pack, comfy_dirs):
    api = pack("api")
    (comfy_dirs.root / "secret.txt").write_text("secret")

    with pytest.raises(ValueError):
        api.LoadWorkflow().load("../../../secret.txt")
