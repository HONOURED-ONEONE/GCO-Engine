import asyncio
import logging
from asyncua import ua, Server

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    
    # Setup namespace
    uri = "http://gco-engine.io"
    idx = await server.register_namespace(uri)
    
    # Add objects
    plant_obj = await server.nodes.objects.add_object(idx, "DigitalTwin")
    
    # Add variables
    temp = await plant_obj.add_variable(idx, "Temperature", 25.0)
    flow = await plant_obj.add_variable(idx, "Flow", 0.0)
    phase = await plant_obj.add_variable(idx, "Phase", "IDLE")
    batch_id = await plant_obj.add_variable(idx, "BatchID", "")
    
    # Shadow setpoints
    temp_shadow = await plant_obj.add_variable(idx, "Temperature_Shadow", 0.0)
    flow_shadow = await plant_obj.add_variable(idx, "Flow_Shadow", 0.0)
    
    # Make them writable
    await temp_shadow.set_writable()
    await flow_shadow.set_writable()
    
    _logger.info("Starting OPC-UA Server...")
    async with server:
        while True:
            # In a real integration, we'd sync these with the TwinService
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
