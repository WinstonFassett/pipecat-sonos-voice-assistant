#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import argparse
import os
import sys

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.mcp_service import MCPClient
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection
from mcp_registry import MCPRegistry
from mcp import StdioServerParameters

load_dotenv(override=True)


async def run_bot(webrtc_connection: SmallWebRTCConnection, _: argparse.Namespace):
    logger.info(f"Starting bot")

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini"
    )
    
    # Load MCP servers from our local registry
    registry = MCPRegistry()
    clients = []
    all_tools = None

    try:
        # Initialize MCP clients for each server in our registry
        registry_servers = registry.get_servers()
        logger.info(f"Found {len(registry_servers)} MCP servers in registry")
        
        for server in registry_servers:
            logger.info(f"Setting up MCP client for server: {server.command}")
            params = StdioServerParameters(
                command=server.command,
                args=server.args,
                env=server.env
            )
            client = MCPClient(server_params=params)
            clients.append(client)
        
        # Collect tools from all MCP clients
        if clients:
            all_standard_tools = []
            for client in clients:
                tools = await client.register_tools(llm)
                all_standard_tools.extend(tools.standard_tools)
            
            all_tools = ToolsSchema(standard_tools=all_standard_tools)
            logger.info(f"Registered {len(all_standard_tools)} tools from MCP servers")
        else:
            logger.warning("No MCP servers found in registry")

    except Exception as e:
        logger.error(f"Error setting up MCP: {e}")
        logger.exception("Error trace:")

    system = f"""
    You are a helpful LLM in a WebRTC call. 
    Your goal is to demonstrate your capabilities in a succinct way. 
    You have access to a number of tools provided by mcp.run. Use any and all tools to help users.
    Your output will be converted to audio so don't include special characters in your answers. 
    Respond to what the user said in a creative and helpful way. 
    When asked for today's date, use 'https://www.datetoday.net/'.
    Don't overexplain what you are doing. 
    Just respond with short sentences when you are carrying out tool calls.
    """

    messages = [{"role": "system", "content": system}]

    context = OpenAILLMContext(messages, all_tools)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            stt,
            context_aggregator.user(),  # User spoken responses
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses and tool context
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected: {client}")
        # Kick off the conversation.
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")

    @transport.event_handler("on_client_closed")
    async def on_client_closed(transport, client):
        logger.info(f"Client closed connection")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


if __name__ == "__main__":
    from run import main

    main()
