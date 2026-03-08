package com.secemumod.demo.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "mod_encryption_key")
public class ModEncryptionKey {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "mod_id")
    private Long modId;

    @Column(name = "file_key_encrypted", columnDefinition = "TEXT")
    private String fileKeyEncrypted;

    @Column(name = "key_version")
    private String keyVersion;

    @Column(name = "encryption_algorithm")
    private String encryptionAlgorithm;

    @Column(name = "creator_id")
    private Long creatorId;

    @Column(name = "is_active")
    private Boolean isActive;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getModId() { return modId; }
    public void setModId(Long modId) { this.modId = modId; }
    public String getFileKeyEncrypted() { return fileKeyEncrypted; }
    public void setFileKeyEncrypted(String fileKeyEncrypted) { this.fileKeyEncrypted = fileKeyEncrypted; }
    public String getKeyVersion() { return keyVersion; }
    public void setKeyVersion(String keyVersion) { this.keyVersion = keyVersion; }
    public String getEncryptionAlgorithm() { return encryptionAlgorithm; }
    public void setEncryptionAlgorithm(String encryptionAlgorithm) { this.encryptionAlgorithm = encryptionAlgorithm; }
    public Long getCreatorId() { return creatorId; }
    public void setCreatorId(Long creatorId) { this.creatorId = creatorId; }
    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }
}
