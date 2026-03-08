package com.secemumod.demo.dto;

import java.util.List;

public class BatchLaunchRequest {
    private List<Long> selectedModIds;
    private String clientPublicKey;
    private String deviceCode;

    public List<Long> getSelectedModIds() { return selectedModIds; }
    public void setSelectedModIds(List<Long> selectedModIds) { this.selectedModIds = selectedModIds; }
    public String getClientPublicKey() { return clientPublicKey; }
    public void setClientPublicKey(String clientPublicKey) { this.clientPublicKey = clientPublicKey; }
    public String getDeviceCode() { return deviceCode; }
    public void setDeviceCode(String deviceCode) { this.deviceCode = deviceCode; }
}
