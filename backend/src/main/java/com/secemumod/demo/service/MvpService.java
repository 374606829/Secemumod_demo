package com.secemumod.demo.service;

import com.secemumod.demo.config.JwtUtil;
import com.secemumod.demo.entity.ModEncryptionKey;
import com.secemumod.demo.entity.ModFile;
import com.secemumod.demo.entity.ModInfo;
import com.secemumod.demo.entity.SysUser;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * Core MVP service: login, batch-launch-secure, file download.
 * <p>
 * MVP simplification: encryptedDek is returned as plaintext Base64 DEK
 * (no RSA envelope encryption), purely for demonstration.
 */
@Service
public class MvpService {
    private static final Logger log = LoggerFactory.getLogger(MvpService.class);

    @PersistenceContext
    private EntityManager em;

    private final JwtUtil jwtUtil;
    private final byte[] masterKey;
    private final String modStoragePath;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public MvpService(
            JwtUtil jwtUtil,
            @Value("${mvp.encryption.master-key}") String masterKeyB64,
            @Value("${mvp.storage.mod-path}") String modStoragePath) {
        this.jwtUtil = jwtUtil;
        this.masterKey = Base64.getDecoder().decode(masterKeyB64);
        this.modStoragePath = modStoragePath;
        if (this.masterKey.length != 32) {
            throw new IllegalArgumentException("MasterKey must decode to 32 bytes, got " + this.masterKey.length);
        }
    }

    // ──────────────────── Login ────────────────────

    public String login(String username, String password) {
        List<SysUser> users = em.createQuery(
                        "SELECT u FROM SysUser u WHERE u.username = :un", SysUser.class)
                .setParameter("un", username)
                .getResultList();
        if (users.isEmpty()) return null;

        SysUser user = users.get(0);
        if (!passwordEncoder.matches(password, user.getPassword())) {
            return null;
        }
        return jwtUtil.generateToken(user.getUsername(), user.getId());
    }

    // ──────────────────── Batch Launch Secure ────────────────────

    /**
     * For each requested mod:
     * 1. Verify mod exists and is APPROVED
     * 2. Decrypt DEK from mod_encryption_key (MasterKey AES-GCM)
     * 3. Return plaintext DEK as Base64 (MVP simplification: no RSA)
     * 4. Return download URLs for mod files
     */
    public Map<String, Object> batchLaunchSecure(List<Long> modIds, String token) {
        String username = jwtUtil.validateAndGetUsername(token);
        if (username == null) {
            throw new SecurityException("Invalid token");
        }

        List<Map<String, Object>> authorizedMods = new ArrayList<>();

        for (Long modId : modIds) {
            // Check mod exists & approved
            List<ModInfo> mods = em.createQuery(
                            "SELECT m FROM ModInfo m WHERE m.id = :id AND m.status = 'APPROVED'", ModInfo.class)
                    .setParameter("id", modId)
                    .getResultList();
            if (mods.isEmpty()) {
                log.warn("Mod {} not found or not approved", modId);
                continue;
            }

            // Get encryption key
            List<ModEncryptionKey> keys = em.createQuery(
                            "SELECT k FROM ModEncryptionKey k WHERE k.modId = :modId AND k.isActive = true",
                            ModEncryptionKey.class)
                    .setParameter("modId", modId)
                    .getResultList();
            if (keys.isEmpty()) {
                log.warn("No active encryption key for mod {}", modId);
                continue;
            }

            // Decrypt DEK (MasterKey + AES-256-GCM)
            String fileKeyEncrypted = keys.get(0).getFileKeyEncrypted();
            byte[] dekPlain;
            try {
                dekPlain = decryptDek(fileKeyEncrypted);
            } catch (Exception e) {
                log.error("Failed to decrypt DEK for mod {}: {}", modId, e.getMessage());
                continue;
            }

            // MVP simplification: return DEK as plaintext Base64 (no RSA encryption)
            String encryptedDek = Base64.getEncoder().encodeToString(dekPlain);

            // Get files
            List<ModFile> files = em.createQuery(
                            "SELECT f FROM ModFile f WHERE f.modId = :modId", ModFile.class)
                    .setParameter("modId", modId)
                    .getResultList();

            List<Map<String, String>> fileList = new ArrayList<>();
            for (ModFile mf : files) {
                Map<String, String> fm = new HashMap<>();
                fm.put("fileName", mf.getFileName());
                fm.put("downloadUrl", "/api/v1/mod/" + modId + "/download/" + mf.getFileName());
                fileList.add(fm);
            }

            Map<String, Object> am = new HashMap<>();
            am.put("modId", modId);
            am.put("encryptedDek", encryptedDek);
            am.put("files", fileList);
            authorizedMods.add(am);
        }

        Map<String, Object> data = new HashMap<>();
        data.put("authorizedMods", authorizedMods);
        return data;
    }

    /**
     * Decrypt DEK: fileKeyEncrypted = Base64(iv[12] + ciphertext + tag[16])
     * Decrypted using MasterKey with AES-256-GCM.
     */
    private byte[] decryptDek(String fileKeyEncryptedB64) throws Exception {
        byte[] raw = Base64.getDecoder().decode(fileKeyEncryptedB64);
        // iv(12) + ciphertext + tag(16)
        if (raw.length < 12 + 16) {
            throw new IllegalArgumentException("Encrypted DEK too short: " + raw.length);
        }
        byte[] iv = Arrays.copyOfRange(raw, 0, 12);
        byte[] ciphertextAndTag = Arrays.copyOfRange(raw, 12, raw.length);

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec spec = new GCMParameterSpec(128, iv);
        cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(masterKey, "AES"), spec);
        return cipher.doFinal(ciphertextAndTag);
    }

    // ──────────────────── File Download ────────────────────

    public byte[] downloadFile(Long modId, String fileName, String token) throws IOException {
        String username = jwtUtil.validateAndGetUsername(token);
        if (username == null) {
            throw new SecurityException("Invalid token");
        }

        List<ModFile> files = em.createQuery(
                        "SELECT f FROM ModFile f WHERE f.modId = :modId AND f.fileName = :fn", ModFile.class)
                .setParameter("modId", modId)
                .setParameter("fn", fileName)
                .getResultList();
        if (files.isEmpty()) {
            throw new IllegalArgumentException("File not found: " + fileName);
        }

        String filePath = files.get(0).getFilePath();
        Path path = Paths.get(filePath);

        // If relative path, resolve against storage dir
        if (!path.isAbsolute()) {
            path = Paths.get(modStoragePath).resolve(filePath);
        }

        if (!Files.exists(path)) {
            throw new IOException("File does not exist on disk: " + path);
        }

        return Files.readAllBytes(path);
    }
}
