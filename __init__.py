"""Custom nodes mappings."""

from .nodes.api import LoadWorkflow, ApiGenerate, ApiSubmit, ApiCollect
from .nodes.grok import GrokGenerate, GrokSubmit, GrokCollect
from .nodes.inference import OpenAIInference


NODE_CLASS_MAPPINGS = {
    # ApiPack/API ####################################################################
    "LoadWorkflow": LoadWorkflow,
    "ApiGenerate": ApiGenerate,
    "ApiSubmit": ApiSubmit,
    "ApiCollect": ApiCollect,
    # ApiPack/Grok ###################################################################
    "GrokGenerate": GrokGenerate,
    "GrokSubmit": GrokSubmit,
    "GrokCollect": GrokCollect,
    # ApiPack/Inference ##############################################################
    "OpenAIInference": OpenAIInference,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    # ApiPack/API ####################################################################
    "LoadWorkflow": "Load Workflow",
    "ApiGenerate": "Api Generate",
    "ApiSubmit": "Api Submit",
    "ApiCollect": "Api Collect",
    # ApiPack/Grok ###################################################################
    "GrokGenerate": "Grok Generate",
    "GrokSubmit": "Grok Submit",
    "GrokCollect": "Grok Collect",
    # ApiPack/Inference ##############################################################
    "OpenAIInference": "OpenAI Inference",
}
