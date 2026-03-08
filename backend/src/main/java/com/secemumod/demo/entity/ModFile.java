package com.secemumod.demo.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "mod_file")
public class ModFile {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "mod_id")
    private Long modId;

    @Column(name = "file_name")
    private String fileName;

    @Column(name = "file_path")
    private String filePath;

    @Column(name = "file_size")
    private Long fileSize;

    @Column(name = "encryption_format")
    private String encryptionFormat;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getModId() { return modId; }
    public void setModId(Long modId) { this.modId = modId; }
    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }
    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public String getEncryptionFormat() { return encryptionFormat; }
    public void setEncryptionFormat(String encryptionFormat) { this.encryptionFormat = encryptionFormat; }
}
