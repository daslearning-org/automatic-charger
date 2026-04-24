package in.daslearning.autocharge;

import android.bluetooth.*;
import android.content.Context;
import java.util.UUID;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;

public class BLEHelper {

    //private BLEListener listener;
    private BluetoothGatt gatt;
    private BluetoothGattCharacteristic writeChar;
    private boolean con_stat = false;
    private boolean uuid_stat = false;

    public BLEHelper() {
    }

    public void connect(Context context, String mac) {

        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        BluetoothDevice device = adapter.getRemoteDevice(mac);

        // clean previous connection
        if (gatt != null) {
            gatt.disconnect();
            gatt.close();
            gatt = null;
        }

        // handle new connection
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            gatt = device.connectGatt(context, false, new BluetoothGattCallback() {

                @Override
                public void onConnectionStateChange(BluetoothGatt g, int status, int newState) {
                    if (newState == BluetoothProfile.STATE_CONNECTED) {
                        Log.d("BLE-AC", "BLE Connected" + status);
                        con_stat = true;
                        new Handler(Looper.getMainLooper()).postDelayed(() -> {
                            g.discoverServices();
                        }, 500);
                    }
                }

                @Override
                public void onServicesDiscovered(BluetoothGatt g, int status) {

                    for (BluetoothGattService service : g.getServices()) {
                        //Log.d("BLE", "Service: " + service.getUuid());

                        for (BluetoothGattCharacteristic ch : service.getCharacteristics()) {
                            //Log.d("BLE", "Char: " + ch.getUuid() + " props=" + ch.getProperties());
                            int props = ch.getProperties();
                            String charUUID = ch.getUuid().toString();
                            if (charUUID.contains("beb5483e")) {
                                writeChar = ch;
                                uuid_stat = true;
                                Log.d("BLE-AC", "Selected UUID: " + charUUID);
                                if((props & BluetoothGattCharacteristic.PROPERTY_WRITE) != 0){
                                    Log.d("BLE-AC", "It is PROPERTY_WRITE");
                                }
                                if((props & BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE) != 0){
                                    Log.d("BLE-AC", "It is PROPERTY_WRITE_NO_RESPONSE");
                                }
                                return;
                            }
                        }
                    }
                }
            },
            BluetoothDevice.TRANSPORT_LE);
        }, 500); // with a delay

    }

    public boolean send(String msg) {
        if (gatt == null || writeChar == null){
            Log.d("BLE-AC", "BLE gatt or write prop is null!");
            return false;
        }
        else{
            writeChar.setValue(msg.getBytes());
            gatt.writeCharacteristic(writeChar);
            Log.d("BLE-AC", "sent to ble: " + msg);
            return true;
        }
    }

    public boolean checkConnectStat(){
        if(con_stat && uuid_stat){
            Log.d("BLE-AC", "Connection is ok & UUID is set");
            return true;
        }
        else{
            return false;
        }
    }

}

// end